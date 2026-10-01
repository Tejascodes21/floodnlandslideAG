import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    brier_score_loss, balanced_accuracy_score, matthews_corrcoef,
    cohen_kappa_score
)
from sklearn.model_selection import KFold, StratifiedKFold
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import existing modules
from ml.data_ingestion import RealDataIngestionPipeline
from ml.feature_engineering import feature_engineer
from ml.config import SEED

MODEL_DIR = Path(__file__).resolve().parent / "model_dir"

# --- PyTorch model definitions ---

class FloodLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=40, hidden_size=32, batch_first=True)
        self.fc = nn.Linear(32, 1)

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        out, _ = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))

class FloodCNNLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv1d(in_channels=1, out_channels=16, kernel_size=3)
        self.lstm = nn.LSTM(input_size=16, hidden_size=32, batch_first=True)
        self.fc = nn.Linear(32, 1)

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        x = torch.relu(self.conv(x))
        x = x.transpose(1, 2)
        out, _ = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))

class LandslideCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=16, kernel_size=3)
        self.conv2 = nn.Conv1d(in_channels=16, out_channels=8, kernel_size=3)
        self.fc = nn.Linear(8, 1)

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = torch.mean(x, dim=2)
        return torch.sigmoid(self.fc(x))

class LandslideLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=40, hidden_size=24, batch_first=True)
        self.fc = nn.Linear(24, 1)

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        out, _ = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))

class PyTorchClassifierWrapper:
    def __init__(self, pytorch_model, name):
        self.model = pytorch_model
        self.name = name
        self.n_features_in_ = 40
        
    def predict_proba(self, X):
        self.model.eval()
        with torch.no_grad():
            x_tensor = torch.tensor(X, dtype=torch.float32)
            probs = self.model(x_tensor).numpy().flatten()
        return np.vstack([1.0 - probs, probs]).T
        
    def predict(self, X, threshold=0.5):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(int)

# --- Calibration Helper ---
def expected_calibration_error(y_true, y_prob, n_bins=10):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    mce = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            diff = np.abs(avg_confidence_in_bin - accuracy_in_bin)
            ece += prop_in_bin * diff
            mce = max(mce, diff)
    return ece, mce

# Reconstruct 40 features as defined in the old documentation
def reconstruct_40_features(df):
    df = df.copy()
    
    # Generate missing core inputs
    if 'sar_backscatter' not in df.columns:
        df['sar_backscatter'] = np.where(
            df['ndwi'] > 0.1, 
            np.clip(-22.0 + df['ndwi'] * 3.0, -25.0, -18.0),
            np.clip(-12.0 + (df['slope'] / 45.0) * 4.0 + (df['ndvi'] * 2.0), -16.0, -6.0)
        )
        
    if 'rain_48h' not in df.columns:
        df['rain_48h'] = (df['rain_24h'] + df['rain_72h']) / 2.0
    if 'sar_vh' not in df.columns:
        df['sar_vh'] = df['sar_backscatter'] - 6.0
    if 'water_occurrence' not in df.columns:
        df['water_occurrence'] = 50.0 + df['ndwi'] * 50.0
        
    # Estimate soil type
    if 'soil_type_encoded' not in df.columns:
        df['soil_type_encoded'] = np.where(df['elevation'] > 1000, 2, np.where(df['slope'] > 15, 1, 0))
        
    # Historical flood frequency
    if 'historical_flood_freq' not in df.columns:
        elev_factor = np.clip(1.0 - df['elevation'] / 500.0, 0, 1)
        drain_factor = np.clip(df['drainage_density'] / 3.0, 0, 1)
        water_factor = np.clip(df['ndwi'], 0, 1)
        rain_factor = np.clip(df['rain_7d'] / 200.0, 0, 1)
        df['historical_flood_freq'] = (elev_factor * 0.35 + drain_factor * 0.25 + water_factor * 0.20 + rain_factor * 0.20) * 10
        
    # Derived interactions
    df['slope_rainfall_interaction'] = df['slope'] * df['rain_72h']
    df['soil_saturation_index'] = df['soil_moisture'] * df['rain_72h']
    df['vegetation_degradation_index'] = (1.0 - df['ndvi']) * df['rain_24h']
    df['terrain_instability_score'] = df['slope'] * df.get('terrain_roughness', 5.0) / (df['ndvi'] + 0.1)
    df['rainfall_accumulation'] = df['rain_24h'] + df['rain_72h'] + df['rain_7d']
    df['river_proximity_factor'] = 1.0 / (df['river_distance'] + 0.1)
    df['upstream_catchment_indicator'] = df['flow_accumulation'] * df['rain_72h']
    df['rain_intensity_24_72'] = np.where(df['rain_72h'] > 0, df['rain_24h'] / df['rain_72h'], 0)
    
    # Missing 40-feature interactions
    df['rain_intensity_48_7d'] = np.where(df['rain_7d'] > 0, df['rain_48h'] / df['rain_7d'], 0)
    df['flood_compound'] = df['rain_24h'] * (1.0 - df['elevation'] / 2500.0)
    df['landslide_compound'] = df['slope'] * df['rain_72h'] * (1.0 - df['ndvi'])
    df['slope_moisture_interaction'] = df['slope'] * df['soil_moisture']
    df['rain_elevation_interaction'] = df['rain_72h'] * df['elevation']
    df['vegetation_vulnerability'] = (1.0 - df['ndvi']) * df['slope']
    df['water_saturation_index'] = df['soil_moisture'] * df['ndwi']
    
    # Log transforms
    df['log_rain_24h'] = np.log1p(df['rain_24h'])
    df['log_rain_72h'] = np.log1p(df['rain_72h'])
    df['log_elevation'] = np.log1p(df['elevation'])
    df['log_flow_acc'] = np.log1p(df['flow_accumulation'])
    
    # Squared terms
    df['slope_squared'] = df['slope'] ** 2
    df['rain_24h_squared'] = df['rain_24h'] ** 2

    aspect = df.get('aspect', 180.0)
    spi = df.get('spi', 0.0)
    terrain_roughness = df.get('terrain_roughness', 5.0)
    curvature = df.get('curvature', 0.0)
    twi = df.get('twi', 10.0)
    mndwi = df.get('mndwi', 0.0)
    evi = df.get('evi', 0.0)

    feature_list_40 = [
        "latitude", "longitude", "elevation", "slope", "aspect", "terrain_roughness", "curvature", "twi", 
        "ndwi", "ndvi", "mndwi", "evi", "rain_24h", "rain_48h", "rain_72h", "rain_7d", "spi", "soil_moisture", 
        "sar_backscatter", "sar_vh", "drainage_density", "river_proximity", "water_occurrence", "flow_accumulation", 
        "soil_type_encoded", "historical_flood_freq", "rain_intensity_24_72", "rain_intensity_48_7d", "flood_compound", 
        "landslide_compound", "slope_moisture_interaction", "rain_elevation_interaction", "vegetation_vulnerability", 
        "water_saturation_index", "log_rain_24h", "log_rain_72h", "log_elevation", "log_flow_acc", "slope_squared", 
        "rain_24h_squared"
    ]
    
    for col in feature_list_40:
        if col not in df.columns:
            if col == 'aspect': df[col] = aspect
            elif col == 'spi': df[col] = spi
            elif col == 'terrain_roughness': df[col] = terrain_roughness
            elif col == 'curvature': df[col] = curvature
            elif col == 'twi': df[col] = twi
            elif col == 'mndwi': df[col] = mndwi
            elif col == 'evi': df[col] = evi
            elif col == 'river_proximity': df[col] = df['river_distance']
            else: df[col] = 0.0
            
    return df[feature_list_40].values

def main():
    print("=================== GEOSHIELD AI PIPELINE AUDIT ===================")
    
    # --- Part 1: Dataset Audit ---
    ingestion = RealDataIngestionPipeline()
    df = ingestion.compile_full_dataset()
    
    print("\n--- PART 1: DATASET AUDIT ---")
    print(f"Dataset Size: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Flood Positives: {df['flood_label'].sum()} ({df['flood_label'].mean()*100:.2f}%)")
    print(f"Landslide Positives: {df['landslide_label'].sum()} ({df['landslide_label'].mean()*100:.2f}%)")
    print(f"Missing Values: {df.isnull().sum().sum()}")
    print(f"Duplicates: {df.duplicated().sum()}")
    print(f"Duplicate Coordinates: {df.duplicated(subset=['latitude', 'longitude']).sum()}")
    
    # Feature engineering for V2 Tree features (31 features)
    df_eng = feature_engineer.engineer_features(df)
    
    if (MODEL_DIR / "feature_cols_v2.pkl").exists():
        tree_features_v2 = joblib.load(MODEL_DIR / "feature_cols_v2.pkl")
    else:
        from ml.config import EXTENDED_FEATURES
        base_cols = [c for c in EXTENDED_FEATURES if c in df_eng.columns]
        eng_cols = feature_engineer.get_engineered_feature_names()
        tree_features_v2 = base_cols + eng_cols
        
    print(f"Dataset features constructed: {len(tree_features_v2)} features")
    
    # --- Part 2: Split Audit ---
    print("\n--- PART 2: SPLIT AUDIT ---")
    states = df['state'].unique()
    print("Unique States in Dataset:", list(states))
    
    from ml.spatial_validation import SpatialCV
    spatial_cv = SpatialCV(group_col="state")
    
    dummy_features = ['latitude', 'longitude']
    _, _, yf_train_val, yf_test, idx_train_val, idx_test = \
        spatial_cv.get_train_test_split(df_eng, dummy_features, "flood_label", test_size=0.20)
    yl_train_val = df_eng["landslide_label"].values[idx_train_val]
    yl_test = df_eng["landslide_label"].values[idx_test]
    
    # Print target distributions
    print(f"Spatial Holdout Split complete: {len(idx_train_val)} train_val, {len(idx_test)} test. Test states: {list(df.iloc[idx_test]['state'].unique())}")
    print(f"  yf_train_val positives: {yf_train_val.sum()}/{len(yf_train_val)}")
    print(f"  yf_test positives: {yf_test.sum()}/{len(yf_test)}")
    print(f"  yl_train_val positives: {yl_train_val.sum()}/{len(yl_train_val)}")
    print(f"  yl_test positives: {yl_test.sum()}/{len(yl_test)}")
    
    # 1. Scale 31 features
    scaler_31 = StandardScaler() if 'StandardScaler' in globals() else None
    if scaler_31 is None:
        from sklearn.preprocessing import StandardScaler
        scaler_31 = StandardScaler()
    scaler_31.fit(df_eng[tree_features_v2].values[idx_train_val])
    X_trainval_31_scaled = scaler_31.transform(df_eng[tree_features_v2].values[idx_train_val])
    X_test_31_scaled = scaler_31.transform(df_eng[tree_features_v2].values[idx_test])

    # 2. Scale 40 features
    X_40 = reconstruct_40_features(df)
    X_trainval_40 = X_40[idx_train_val]
    X_test_40 = X_40[idx_test]
    
    scaler_40 = StandardScaler()
    X_trainval_40_scaled = scaler_40.fit_transform(X_trainval_40)
    X_test_40_scaled = scaler_40.transform(X_test_40)
    
    # --- Load all models ---
    print("\n--- LOADING MODELS ---")
    models = {}
    
    # Load Tree models
    tree_models = {
        "XGBoost Flood": "flood_v2_xgb.pkl",
        "LightGBM Flood": "flood_v2_lgb.pkl",
        "Random Forest Flood": "flood_v2_rf.pkl",
        "XGBoost Landslide": "landslide_v2_xgb.pkl",
        "LightGBM Landslide": "landslide_v2_lgb.pkl",
        "Random Forest Landslide": "landslide_v2_rf.pkl"
    }
    
    for name, fn in tree_models.items():
        fpath = MODEL_DIR / fn
        if fpath.exists():
            models[name] = (joblib.load(fpath), "tree")
            print(f"Loaded {name} (Tree).")
            
    # Load PyTorch models
    pytorch_models = {
        "LSTM Flood": (FloodLSTM(), "flood_v2_lstm.pth"),
        "CNN-LSTM Flood": (FloodCNNLSTM(), "flood_v2_cnn_lstm.pth"),
        "CNN Landslide": (LandslideCNN(), "landslide_v2_cnn.pth"),
        "LSTM Landslide": (LandslideLSTM(), "landslide_v2_lstm.pth")
    }
    
    for name, (model, fn) in pytorch_models.items():
        fpath = MODEL_DIR / fn
        if fpath.exists():
            try:
                state_dict = torch.load(fpath, map_location="cpu")
                model.load_state_dict(state_dict)
                models[name] = (PyTorchClassifierWrapper(model, name), "pytorch")
                print(f"Loaded {name} (PyTorch).")
            except Exception as e:
                print(f"Error loading PyTorch {name}: {e}")

    # Ensembles
    class EnsembleWrapper:
        def __init__(self, constituents, weights):
            self.constituents = constituents
            self.weights = weights
            
        def predict_proba(self, X_31, X_40):
            probs = np.zeros(X_31.shape[0])
            total_w = sum(self.weights)
            for (m, mtype), w in zip(self.constituents, self.weights):
                expected_n = getattr(m, 'n_features_in_', 40)
                X_in = X_40 if expected_n == 40 else X_31
                probs += m.predict_proba(X_in)[:, 1] * w
            probs /= total_w
            return np.vstack([1.0 - probs, probs]).T
            
        def predict(self, X_31, X_40, threshold=0.5):
            return (self.predict_proba(X_31, X_40)[:, 1] >= threshold).astype(int)

    # Blend Flood Ensemble
    flood_blend = []
    flood_blend_w = []
    for k, w in [("XGBoost Flood", 0.35), ("LightGBM Flood", 0.35), ("LSTM Flood", 0.15), ("CNN-LSTM Flood", 0.15)]:
        if k in models:
            flood_blend.append(models[k])
            flood_blend_w.append(w)
    if flood_blend:
        models["Ensemble Flood"] = (EnsembleWrapper(flood_blend, flood_blend_w), "ensemble")
        print("Assembled Ensemble Flood.")
        
    # Blend Landslide Ensemble
    slide_blend = []
    slide_blend_w = []
    for k, w in [("Random Forest Landslide", 0.25), ("XGBoost Landslide", 0.35), ("LightGBM Landslide", 0.20), ("CNN Landslide", 0.10), ("LSTM Landslide", 0.10)]:
        if k in models:
            slide_blend.append(models[k])
            slide_blend_w.append(w)
    if slide_blend:
        models["Ensemble Landslide"] = (EnsembleWrapper(slide_blend, slide_blend_w), "ensemble")
        print("Assembled Ensemble Landslide.")

    # Compute metrics separately for every model
    def evaluate_model_on_data(name, wrapper, mtype, X_31_s, X_40_s, y_true):
        if mtype == "tree":
            expected_n = getattr(wrapper, 'n_features_in_', 40)
            X_in = X_40_s if expected_n == 40 else X_31_s
            y_pred = wrapper.predict(X_in)
            probs = wrapper.predict_proba(X_in)[:, 1]
        elif mtype == "pytorch":
            y_pred = wrapper.predict(X_40_s)
            probs = wrapper.predict_proba(X_40_s)[:, 1]
        else: # ensemble
            y_pred = wrapper.predict(X_31_s, X_40_s)
            probs = wrapper.predict_proba(X_31_s, X_40_s)[:, 1]
            
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        try:
            auc = roc_auc_score(y_true, probs)
        except Exception:
            auc = np.nan
            
        try:
            pr_auc = average_precision_score(y_true, probs)
        except Exception:
            pr_auc = np.nan
            
        bal_acc = balanced_accuracy_score(y_true, y_pred)
        mcc = matthews_corrcoef(y_true, y_pred)
        kappa = cohen_kappa_score(y_true, y_pred)
        brier = brier_score_loss(y_true, probs)
        ece, mce = expected_calibration_error(y_true, probs)
        
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (cm[0,0], 0, 0, 0)
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        
        return {
            "accuracy": acc * 100,
            "precision": prec * 100,
            "recall": rec * 100,
            "specificity": specificity * 100,
            "f1": f1 * 100,
            "auc": auc * 100 if not np.isnan(auc) else 0.0,
            "pr_auc": pr_auc * 100 if not np.isnan(pr_auc) else 0.0,
            "balanced_accuracy": bal_acc * 100,
            "mcc": mcc,
            "cohen_kappa": kappa,
            "brier_score": brier,
            "ece": ece,
            "mce": mce,
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
        }

    # Evaluate on Spatial holdout test set
    print("\n--- PART 3: MODEL AUDIT METRICS ---")
    print(f"\nEvaluating models on Spatial holdout test set:")
    print(f"{'Model':<30} | {'Acc':>6} | {'F1':>6} | {'AUC':>6} | {'Brier':>6} | {'ECE':>6}")
    print("-" * 75)
    
    test_metrics = {}
    for name, (model, mtype) in sorted(models.items()):
        y_target = yf_test if "Flood" in name else yl_test
        stats = evaluate_model_on_data(name, model, mtype, X_test_31_scaled, X_test_40_scaled, y_target)
        test_metrics[name] = stats
        print(f"{name:<30} | {stats['accuracy']:>6.2f} | {stats['f1']:>6.2f} | {stats['auc']:>6.2f} | {stats['brier_score']:>6.4f} | {stats['ece']:>6.4f}")
        
    print("\nEvaluating models on Train+Val set (seen districts):")
    print(f"{'Model':<30} | {'Acc':>6} | {'F1':>6} | {'AUC':>6} | {'Brier':>6} | {'ECE':>6}")
    print("-" * 75)
    trainval_metrics = {}
    for name, (model, mtype) in sorted(models.items()):
        y_target = yf_train_val if "Flood" in name else yl_train_val
        stats = evaluate_model_on_data(name, model, mtype, X_trainval_31_scaled, X_trainval_40_scaled, y_target)
        trainval_metrics[name] = stats
        print(f"{name:<30} | {stats['accuracy']:>6.2f} | {stats['f1']:>6.2f} | {stats['auc']:>6.2f} | {stats['brier_score']:>6.4f} | {stats['ece']:>6.4f}")

    # --- Part 13: Robustness Analysis ---
    print("\n--- PART 13: ROBUSTNESS ANALYSIS ---")
    # Shift rain features by +50mm
    rain_24_idx = tree_features_v2.index("rain_24h")
    rain_72_idx = tree_features_v2.index("rain_72h")
    
    print("Stress test: adding +50mm rainfall to the test set features...")
    X_test_tree_perturbed = df_eng[tree_features_v2].values[idx_test].copy()
    X_test_tree_perturbed[:, rain_24_idx] += 50.0
    X_test_tree_perturbed[:, rain_72_idx] += 50.0
    
    # Recompute engineered columns for tree models
    slope_idx = tree_features_v2.index("slope")
    sm_idx = tree_features_v2.index("soil_moisture")
    ndvi_idx = tree_features_v2.index("ndvi")
    rain_7d_idx = tree_features_v2.index("rain_7d")
    flow_acc_idx = tree_features_v2.index("flow_accumulation")
    
    if "slope_rainfall_interaction" in tree_features_v2:
        idx = tree_features_v2.index("slope_rainfall_interaction")
        X_test_tree_perturbed[:, idx] = X_test_tree_perturbed[:, slope_idx] * X_test_tree_perturbed[:, rain_72_idx]
    if "soil_saturation_index" in tree_features_v2:
        idx = tree_features_v2.index("soil_saturation_index")
        X_test_tree_perturbed[:, idx] = X_test_tree_perturbed[:, sm_idx] * X_test_tree_perturbed[:, rain_72_idx]
    if "vegetation_degradation_index" in tree_features_v2:
        idx = tree_features_v2.index("vegetation_degradation_index")
        X_test_tree_perturbed[:, idx] = (1.0 - X_test_tree_perturbed[:, ndvi_idx]) * X_test_tree_perturbed[:, rain_24_idx]
    if "rainfall_accumulation" in tree_features_v2:
        idx = tree_features_v2.index("rainfall_accumulation")
        X_test_tree_perturbed[:, idx] = X_test_tree_perturbed[:, rain_24_idx] + X_test_tree_perturbed[:, rain_72_idx] + X_test_tree_perturbed[:, rain_7d_idx]
    if "upstream_catchment_indicator" in tree_features_v2:
        idx = tree_features_v2.index("upstream_catchment_indicator")
        X_test_tree_perturbed[:, idx] = X_test_tree_perturbed[:, flow_acc_idx] * X_test_tree_perturbed[:, rain_72_idx]
        
    X_test_tree_perturbed_scaled = scaler_31.transform(X_test_tree_perturbed)
    
    # Do the same for 40-feature array
    df_perturbed = df.iloc[idx_test].copy()
    df_perturbed['rain_24h'] += 50.0
    df_perturbed['rain_72h'] += 50.0
    df_perturbed['rain_7d'] += 50.0
    
    X_test_40_perturbed = reconstruct_40_features(df_perturbed)
    X_test_40_perturbed_scaled = scaler_40.transform(X_test_40_perturbed)
    
    print("\nRobustness metrics under +50mm rain shift:")
    print(f"{'Model':<30} | {'Original Acc':>12} | {'Robustness Acc':>14} | {'Degradation':>12}")
    print("-" * 75)
    for name, (model, mtype) in sorted(models.items()):
        y_target = yf_test if "Flood" in name else yl_test
        orig_stats = test_metrics[name]
        robust_stats = evaluate_model_on_data(name, model, mtype, X_test_tree_perturbed_scaled, X_test_40_perturbed_scaled, y_target)
        degr = orig_stats['accuracy'] - robust_stats['accuracy']
        print(f"{name:<30} | {orig_stats['accuracy']:>11.2f}% | {robust_stats['accuracy']:>13.2f}% | {degr:>11.2f}%")

if __name__ == "__main__":
    main()
