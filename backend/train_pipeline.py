import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier

def build_and_train_models():
    print("=================== GeoShield AI Model Training Pipeline ===================")
    
    # 1. Ensure output directory exists
    model_dir = Path("model_dir")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Generate synthetic geospatial hazard dataset (realistic joint distributions)
    print("Generating synthetic multi-spectral and terrain dataset...")
    n_samples = 2500
    np.random.seed(42)
    
    # Raw physical inputs
    lat = np.random.uniform(15.0, 30.0, n_samples)
    lon = np.random.uniform(70.0, 95.0, n_samples)
    elevation = np.random.uniform(5.0, 1800.0, n_samples)
    
    # Slope (higher elevation tends to have steeper mountain faces)
    slope = np.clip(np.random.uniform(0.5, 45.0, n_samples) * (1.0 + (elevation / 1800.0) * 0.5), 0.5, 45.0)
    
    # NDWI (Water body: values > 0.1 simulate river deltas/basins at low elevations)
    ndwi = np.random.uniform(-0.8, 0.6, n_samples)
    
    # NDVI (Vegetation: higher on moderate slopes/lowlands, lower on sandy or high-alpine peaks)
    ndvi = np.random.uniform(-0.1, 0.85, n_samples)
    
    # Precipitation accumulators (Storm simulations)
    rain_24h = np.random.exponential(scale=25.0, size=n_samples)
    rain_72h = rain_24h + np.random.exponential(scale=35.0, size=n_samples)
    
    # Soil Moisture (highly correlated with rainfall and vegetation density)
    soil_moisture = np.clip(20.0 + (rain_72h * 0.15) + (ndvi * 30.0) + np.random.normal(0, 5, n_samples), 5.0, 95.0)
    
    # Sentinel-1 SAR Backscatter (low on water pools, high on rough, rocky slopes)
    sar_backscatter = np.where(ndwi > 0.1, -22.0 + ndwi * 3.0, -12.0 + (slope / 45.0) * 4.0 + np.random.normal(0, 1.5, n_samples))
    
    # Define continuous hazard risk scores for physical modeling
    flood_score = (
        (rain_24h > 50.0).astype(float) * 0.25 +
        (ndwi > 0.05).astype(float) * 0.15 +
        (elevation < 400.0).astype(float) * 0.15 +
        (soil_moisture > 70.0).astype(float) * 0.15 +
        (rain_72h > 100.0).astype(float) * 0.10
    )
    
    landslide_score = (
        (slope > 20.0).astype(float) * 0.25 +
        (soil_moisture > 60.0).astype(float) * 0.15 +
        (rain_72h > 100.0).astype(float) * 0.15 +
        (ndvi < 0.3).astype(float) * 0.15 +
        (elevation > 500.0).astype(float) * 0.10
    )
    
    # Use top 25% for flood and landslide occurrences to ensure balance
    flood_occurred = (flood_score >= np.percentile(flood_score, 75)).astype(int)
    landslide_occurred = (landslide_score >= np.percentile(landslide_score, 75)).astype(int)
    
    # Assemble DataFrame
    df = pd.DataFrame({
        "lat": lat, "lon": lon,
        "elevation": elevation, "slope": slope,
        "ndwi": ndwi, "ndvi": ndvi,
        "rain_24h": rain_24h, "rain_72h": rain_72h,
        "soil_moisture": soil_moisture,
        "sar_backscatter": sar_backscatter,
        "flood_occurred": flood_occurred,
        "landslide_occurred": landslide_occurred
    })
    
    # 3. Define features
    feature_cols = ["lat", "lon", "elevation", "slope", "ndwi", "ndvi", "rain_24h", "rain_72h", "soil_moisture", "sar_backscatter"]
    X = df[feature_cols].values
    y_flood = df["flood_occurred"].values
    y_slide = df["landslide_occurred"].values
    
    # Save feature names list
    joblib.dump(feature_cols, model_dir / "feature_cols.pkl")
    
    # 4. Split and Scale Datasets
    indices = np.arange(len(X))
    strata = y_flood.astype(int) * 2 + y_slide.astype(int)
    idx_train, idx_test = train_test_split(indices, test_size=0.2, random_state=42, stratify=strata)

    X_train, X_test = X[idx_train], X[idx_test]
    y_f_train, y_f_test = y_flood[idx_train], y_flood[idx_test]
    y_s_train, y_s_test = y_slide[idx_train], y_slide[idx_test]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save the fitted scaler
    joblib.dump(scaler, model_dir / "scaler.pkl")
    
    # 5. Train Flood Model: XGBoost Classifier
    print("Training Flood Prediction Model (XGBoost Ensemble)...")
    xgb_flood = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.08, random_state=42)
    xgb_flood.fit(X_train_scaled, y_f_train)
    joblib.dump(xgb_flood, model_dir / "xgb_flood.pkl")
    
    # 6. Train Landslide Model: Random Forest Classifier
    print("Training Landslide Susceptibility Model (Random Forest)...")
    rf_landslide = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    rf_landslide.fit(X_train_scaled, y_s_train)
    joblib.dump(rf_landslide, model_dir / "rf_landslide.pkl")
    
    # 7. Train Sequential Deep Learning Model: MLPClassifier (as PyTorch/LSTM Emulator)
    print("Training Sequential DL Risk Estimator (Multi-Layer Perceptron)...")
    mlp_seq = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=200, random_state=42)
    mlp_seq.fit(X_train_scaled, y_f_train)  # Trains dynamic feature weighting
    joblib.dump(mlp_seq, model_dir / "mlp_seq.pkl")
    
    # 8. Evaluate Metrics on Test Set
    pred_f = xgb_flood.predict(X_test_scaled)
    pred_s = rf_landslide.predict(X_test_scaled)
    
    print("\n--- Model Evaluation Summary ---")
    print(f"Dataset Shape: {df.shape}")
    print(f"Total Positive Flood Cases: {np.sum(y_flood)} | Total Positive Landslide Cases: {np.sum(y_slide)}")
    
    print("\n[Flood Model Metrics - XGBoost]")
    print(f"  Accuracy:  {accuracy_score(y_f_test, pred_f)*100:.2f}%")
    print(f"  Precision: {precision_score(y_f_test, pred_f)*100:.2f}%")
    print(f"  Recall:    {recall_score(y_f_test, pred_f)*100:.2f}%")
    print(f"  F1-Score:  {f1_score(y_f_test, pred_f)*100:.2f}%")
    print(f"  ROC-AUC:   {roc_auc_score(y_f_test, xgb_flood.predict_proba(X_test_scaled)[:, 1])*100:.2f}%")
    
    print("\n[Landslide Model Metrics - Random Forest]")
    print(f"  Accuracy:  {accuracy_score(y_s_test, pred_s)*100:.2f}%")
    print(f"  Precision: {precision_score(y_s_test, pred_s)*100:.2f}%")
    print(f"  Recall:    {recall_score(y_s_test, pred_s)*100:.2f}%")
    print(f"  F1-Score:  {f1_score(y_s_test, pred_s)*100:.2f}%")
    print(f"  ROC-AUC:   {roc_auc_score(y_s_test, rf_landslide.predict_proba(X_test_scaled)[:, 1])*100:.2f}%")
    
    print("\nAll models trained and saved to model_dir/ directory successfully.")
    print("===========================================================================")

if __name__ == "__main__":
    build_and_train_models()
