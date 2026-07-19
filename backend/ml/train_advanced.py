"""
Refactored Master Training Orchestrator
=========================================
Triggers real-data ingestion, engineers features, splits datasets spatially,
tunes models via Optuna, trains PyTorch deep learning models, applies probability
calibration, registers models, and audits performance for data leakage.

Usage:
    cd backend
    python -m ml.train_advanced
"""

import sys
import os
import logging
import time
import json
import numpy as np
import pandas as pd
from pathlib import Path
import joblib
import torch
from sklearn.calibration import CalibratedClassifierCV

# Resolve FrozenEstimator import based on scikit-learn version
try:
    from sklearn.frozen import FrozenEstimator
    HAS_FROZEN = True
except ImportError:
    try:
        from sklearn.calibration import FrozenEstimator
        HAS_FROZEN = True
    except ImportError:
        HAS_FROZEN = False

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("geoshield.ml.train")

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.data_ingestion import RealDataIngestionPipeline
from ml.spatial_validation import SpatialCV
from ml.feature_engineering import feature_engineer
from ml.flood_models import FloodModelSuite
from ml.landslide_models import LandslideModelSuite
from ml.deep_learning_models import (
    FloodLSTM, FloodCNNLSTM, LandslideCNN, LandslideLSTM, PyTorchClassifierWrapper
)
from ml.evaluation import evaluator
from ml.config import SEED

MODEL_DIR = Path(__file__).resolve().parent.parent / "model_dir"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def audit_performance_leakage(hazard_name: str, accuracy: float, df: pd.DataFrame):
    """Checks for target leakage, duplicate records, or spatial leaks if score is > 98%."""
    if accuracy > 98.0:
        logger.warning(f"⚠️ DANGER: Artificially inflated {hazard_name} accuracy detected ({accuracy}% > 98%).")
        logger.warning("Performing automated leakage audit...")
        
        # 1. Check for duplicates
        dupes = df.duplicated(subset=["latitude", "longitude"]).sum()
        logger.warning(f"  [Audit 1/4] Found {dupes} coordinate duplicates in dataset.")
        
        # 2. Check label leakage in features
        corr_scores = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            if col not in ["flood_label", "landslide_label", "flood_occurred", "landslide_occurred"]:
                corr = df[col].corr(df[hazard_name.lower() + "_label"])
                corr_scores[col] = abs(corr)
                
        high_corr = {k: round(v, 3) for k, v in corr_scores.items() if v > 0.95}
        if high_corr:
            logger.warning(f"  [Audit 2/4] Extreme feature correlations found (target leakage risk): {high_corr}")
        else:
            logger.info("  [Audit 2/4] No extreme direct correlation leaks found.")
            
        # 3. Check spatial partition leaks
        logger.warning("  [Audit 3/4] Check: Ensure training and testing districts are completely separate.")
        
        # 4. Check rule leakage
        logger.warning("  [Audit 4/4] Check: Confirm labels are historical events, not derived using formulas.")
        print("-" * 60)
    else:
        logger.info(f"Leakage audit: {hazard_name} accuracy is within realistic range ({accuracy}%).")


def train_advanced_pipeline():
    """Master training orchestrator."""
    start_time = time.time()
    print("=" * 80)
    print("  GeoShield AI — Real-Data ML/DL Training Pipeline v2.0")
    print("=" * 80)
    
    # 1. Ingest real-world datasets
    print("\n[Step 1/6] Ingesting real historical geospatial hazard dataset...")
    ingestion = RealDataIngestionPipeline()
    df = ingestion.compile_full_dataset()
    
    print(f"  Dataset shape: {df.shape}")
    print(f"  Flood positives: {df['flood_label'].sum()} ({df['flood_label'].mean()*100:.1f}%)")
    print(f"  Landslide positives: {df['landslide_label'].sum()} ({df['landslide_label'].mean()*100:.1f}%)")
    
    # 2. Feature engineering
    print("\n[Step 2/6] Running feature engineering pipeline...")
    df_engineered = feature_engineer.engineer_features(df)
    
    # Get feature columns
    all_feature_cols = feature_engineer.get_feature_names()
    print(f"  Total features for training: {len(all_feature_cols)}")
    
    # 3. Spatial train/validation/test split
    print("\n[Step 3/6] Splitting datasets spatially (GroupKFold by State)...")
    spatial_cv = SpatialCV(group_col="state")
    
    # Split out test set (20%)
    X_train_val, X_test, yf_train_val, yf_test, idx_train_val, idx_test = spatial_cv.get_train_test_split(
        df_engineered, all_feature_cols, "flood_label", test_size=0.20
    )
    yl_train_val = df_engineered["landslide_label"].values[idx_train_val]
    yl_test = df_engineered["landslide_label"].values[idx_test]
    
    # Split remainder spatially into train (80%) and validation (20%)
    df_train_val = df_engineered.iloc[idx_train_val].reset_index(drop=True)
    X_train, X_val, yf_train, yf_val, idx_train, idx_val = spatial_cv.get_train_test_split(
        df_train_val, all_feature_cols, "flood_label", test_size=0.20
    )
    yl_train = yl_train_val[idx_train]
    yl_val = yl_train_val[idx_val]
    
    print(f"  Train records: {X_train.shape[0]} | Val: {X_val.shape[0]} | Test: {X_test.shape[0]}")
    
    # Scale features
    X_train_scaled = feature_engineer.fit_scaler(X_train)
    X_val_scaled = feature_engineer.transform(X_val)
    X_test_scaled = feature_engineer.transform(X_test)
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save fitted scaler and feature configuration
    joblib.dump(feature_engineer.scaler, MODEL_DIR / "scaler_v2.pkl")
    joblib.dump(all_feature_cols, MODEL_DIR / "feature_cols_v2.pkl")
    
    # Save V1 versions for backward-compatibility fallback support
    joblib.dump(feature_engineer.scaler, MODEL_DIR / "scaler.pkl")
    joblib.dump(all_feature_cols, MODEL_DIR / "feature_cols.pkl")
    
    # 4. Train flood models (XGBoost, LightGBM, CatBoost with Optuna)
    print("\n[Step 4/6] Training Flood Prediction Ensemble (Bayesian Tuning & Calibration)...")
    print("-" * 65)
    flood_suite = FloodModelSuite()
    flood_suite.train_all(X_train_scaled, yf_train, X_val_scaled, yf_val)
    
    # Calibrate Tree models on validation data
    calibrated_flood_models = {}
    for name, model in flood_suite.models.items():
        logger.info(f"Calibrating Flood {name} model probabilities...")
        if HAS_FROZEN:
            frozen_model = FrozenEstimator(model)
            calibrated_model = CalibratedClassifierCV(estimator=frozen_model, method="sigmoid")
        else:
            calibrated_model = CalibratedClassifierCV(estimator=model, method="sigmoid", cv="prefit")
        calibrated_model.fit(X_val_scaled, yf_val)
        calibrated_flood_models[name] = calibrated_model
        
    flood_suite.models = calibrated_flood_models
    flood_suite.save_models("flood_v2")
    
    # Save best single classifier (XGBoost) as V1 model for self-healing API fallback
    if "xgb" in flood_suite.models:
        joblib.dump(flood_suite.models["xgb"], MODEL_DIR / "xgb_flood.pkl")
        logger.info("Saved Best Calibrated Flood XGBoost model as V1 fallback.")

    # Train Flood Deep Learning Models
    print("\nTraining Flood Deep Learning models (LSTM & CNN-LSTM)...")
    flood_lstm = PyTorchClassifierWrapper(FloodLSTM(), model_name="FloodLSTM")
    flood_lstm.fit(X_train_scaled, yf_train, X_val_scaled, yf_val)
    torch.save(flood_lstm.model.state_dict(), MODEL_DIR / "flood_v2_lstm.pth")
    logger.info("Saved FloodLSTM model state.")

    flood_cnnlstm = PyTorchClassifierWrapper(FloodCNNLSTM(), model_name="FloodCNNLSTM")
    flood_cnnlstm.fit(X_train_scaled, yf_train, X_val_scaled, yf_val)
    torch.save(flood_cnnlstm.model.state_dict(), MODEL_DIR / "flood_v2_cnn_lstm.pth")
    logger.info("Saved FloodCNNLSTM model state.")
        
    # Evaluate flood suite
    eval_models = {k: v for k, v in flood_suite.models.items()}
    eval_models["lstm"] = flood_lstm
    eval_models["cnn_lstm"] = flood_cnnlstm
    
    flood_results = evaluator.evaluate_suite(eval_models, X_test_scaled, yf_test, "flood")
    
    # Ensemble blending prediction
    flood_ens_proba = np.zeros(X_test_scaled.shape[0])
    total_w = 0.0
    for name, w in [("xgb", 0.35), ("lgb", 0.35), ("cat", 0.15), ("lstm", 0.075), ("cnn_lstm", 0.075)]:
        if name in eval_models:
            flood_ens_proba += eval_models[name].predict_proba(X_test_scaled)[:, 1] * w
            total_w += w
    flood_ens_proba /= total_w
    
    flood_ens_pred = (flood_ens_proba >= 0.5).astype(int)
    flood_ens_metrics = evaluator.evaluate_model(yf_test, flood_ens_pred, flood_ens_proba, "flood_ensemble")
    flood_results["ensemble"] = flood_ens_metrics
    
    print(f"\n  Flood Ensemble: Acc={flood_ens_metrics['accuracy']}% | F1={flood_ens_metrics['f1_score']}% | AUC={flood_ens_metrics.get('roc_auc', 'N/A')}%")
    audit_performance_leakage("Flood", flood_ens_metrics["accuracy"], df)
    
    # 5. Train landslide models (Random Forest, XGBoost, LightGBM with Optuna)
    print("\n[Step 5/6] Training Landslide Susceptibility Ensemble (Bayesian Tuning & Calibration)...")
    print("-" * 65)
    landslide_suite = LandslideModelSuite()
    landslide_suite.train_all(X_train_scaled, yl_train, X_val_scaled, yl_val)
    
    # Calibrate Tree models on validation data
    calibrated_landslide_models = {}
    for name, model in landslide_suite.models.items():
        logger.info(f"Calibrating Landslide {name} model probabilities...")
        if HAS_FROZEN:
            frozen_model = FrozenEstimator(model)
            calibrated_model = CalibratedClassifierCV(estimator=frozen_model, method="sigmoid")
        else:
            calibrated_model = CalibratedClassifierCV(estimator=model, method="sigmoid", cv="prefit")
        calibrated_model.fit(X_val_scaled, yl_val)
        calibrated_landslide_models[name] = calibrated_model
        
    landslide_suite.models = calibrated_landslide_models
    landslide_suite.save_models("landslide_v2")
    
    # Save best single classifier (Random Forest) as V1 model for self-healing API fallback
    if "rf" in landslide_suite.models:
        joblib.dump(landslide_suite.models["rf"], MODEL_DIR / "rf_landslide.pkl")
        logger.info("Saved Best Calibrated Landslide Random Forest model as V1 fallback.")

    # Train Landslide Deep Learning Models
    print("\nTraining Landslide Deep Learning models (CNN & LSTM)...")
    slide_cnn = PyTorchClassifierWrapper(LandslideCNN(), model_name="LandslideCNN")
    slide_cnn.fit(X_train_scaled, yl_train, X_val_scaled, yl_val)
    torch.save(slide_cnn.model.state_dict(), MODEL_DIR / "landslide_v2_cnn.pth")
    logger.info("Saved LandslideCNN model state.")

    slide_lstm = PyTorchClassifierWrapper(LandslideLSTM(), model_name="LandslideLSTM")
    slide_lstm.fit(X_train_scaled, yl_train, X_val_scaled, yl_val)
    torch.save(slide_lstm.model.state_dict(), MODEL_DIR / "landslide_v2_lstm.pth")
    logger.info("Saved LandslideLSTM model state.")
        
    # Evaluate landslide suite
    eval_slide_models = {k: v for k, v in landslide_suite.models.items()}
    eval_slide_models["cnn"] = slide_cnn
    eval_slide_models["lstm"] = slide_lstm
    
    landslide_results = evaluator.evaluate_suite(eval_slide_models, X_test_scaled, yl_test, "landslide")
    
    # Ensemble blending prediction
    landslide_ens_proba = np.zeros(X_test_scaled.shape[0])
    total_wl = 0.0
    for name, w in [("rf", 0.25), ("xgb", 0.35), ("lgb", 0.20), ("cnn", 0.10), ("lstm", 0.10)]:
        if name in eval_slide_models:
            landslide_ens_proba += eval_slide_models[name].predict_proba(X_test_scaled)[:, 1] * w
            total_wl += w
    landslide_ens_proba /= total_wl
    
    landslide_ens_pred = (landslide_ens_proba >= 0.5).astype(int)
    landslide_ens_metrics = evaluator.evaluate_model(yl_test, landslide_ens_pred, landslide_ens_proba, "landslide_ensemble")
    landslide_results["ensemble"] = landslide_ens_metrics
    
    print(f"\n  Landslide Ensemble: Acc={landslide_ens_metrics['accuracy']}% | F1={landslide_ens_metrics['f1_score']}% | AUC={landslide_ens_metrics.get('roc_auc', 'N/A')}%")
    audit_performance_leakage("Landslide", landslide_ens_metrics["accuracy"], df)
    
    # 6. Extract Feature Importance
    print("\n[Step 6/6] Summarizing feature importance rankings...")
    flood_importance = flood_suite.get_feature_importance(all_feature_cols)
    landslide_importance = landslide_suite.get_feature_importance(all_feature_cols)
    
    print("\n  Top 5 Flood Drivers:")
    for feat in flood_importance[:5]:
        print(f"    {feat['feature']}: {feat['importance']:.4f}")
        
    print("\n  Top 5 Landslide Drivers:")
    for feat in landslide_importance[:5]:
        print(f"    {feat['feature']}: {feat['importance']:.4f}")
        
    # Generate ROC curve data for dashboard charts
    roc_flood = evaluator.generate_roc_data(yf_test, flood_ens_proba)
    roc_slide = evaluator.generate_roc_data(yl_test, landslide_ens_proba)
    
    # Save results dictionary
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_results = {
        "dataset": {
            "n_samples": len(df),
            "n_features": len(all_feature_cols),
            "features": all_feature_cols
        },
        "flood_models": flood_results,
        "landslide_models": landslide_results,
        "flood_feature_importance": flood_importance[:20],
        "landslide_feature_importance": landslide_importance[:20],
        "roc_data": {
            "flood": roc_flood,
            "landslide": roc_slide
        },
        "training_time_seconds": round(time.time() - start_time, 1)
    }
    
    evaluator.save_results(all_results, "advanced_evaluation_v2.json")
    
    elapsed = time.time() - start_time
    print(f"\n{'=' * 80}")
    print(f"  Training Pipeline execution successful in {elapsed:.1f}s")
    print(f"  Models successfully saved to: {MODEL_DIR}")
    print(f"  Results saved to: {RESULTS_DIR}")
    print(f"{'=' * 80}")
    
    return all_results


if __name__ == "__main__":
    train_advanced_pipeline()
