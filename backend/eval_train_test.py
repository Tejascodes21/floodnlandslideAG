"""
Evaluate all models on both Training and Testing sets.
Reproduces the same data splits used in train_advanced.py,
then loads saved models and computes metrics on both sets.
"""

import sys, os, json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ml.data_ingestion import RealDataIngestionPipeline
from ml.spatial_validation import SpatialCV
from ml.feature_engineering import feature_engineer
from ml.config import EXTENDED_FEATURES

MODEL_DIR = Path(__file__).resolve().parent / "model_dir"


def evaluate(name, model, X, y):
    """Return dict of metrics for a single model on a single split."""
    y_pred = model.predict(X)
    metrics = {
        "accuracy": round(accuracy_score(y, y_pred) * 100, 2),
        "precision": round(precision_score(y, y_pred, zero_division=0) * 100, 2),
        "recall": round(recall_score(y, y_pred, zero_division=0) * 100, 2),
        "f1_score": round(f1_score(y, y_pred, zero_division=0) * 100, 2),
    }
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X)[:, 1]
            metrics["roc_auc"] = round(roc_auc_score(y, proba) * 100, 2)
        except Exception:
            metrics["roc_auc"] = "N/A"
    return metrics


def main():
    # ---- 1. Reproduce the exact data splits ----
    print("=" * 80)
    print("  GeoShield AI — Training vs Testing Accuracy Report")
    print("=" * 80)

    print("\n[1/4] Ingesting dataset...")
    ingestion = RealDataIngestionPipeline()
    df = ingestion.compile_full_dataset()

    print(f"  Dataset shape: {df.shape}")
    print(f"  Flood positives: {df['flood_label'].sum()} ({df['flood_label'].mean()*100:.1f}%)")
    print(f"  Landslide positives: {df['landslide_label'].sum()} ({df['landslide_label'].mean()*100:.1f}%)")

    print("\n[2/4] Running feature engineering...")
    df_eng = feature_engineer.engineer_features(df)
    base_cols = [c for c in EXTENDED_FEATURES if c in df_eng.columns]
    eng_cols = feature_engineer.get_engineered_feature_names()
    all_feature_cols = base_cols + eng_cols

    X = df_eng[all_feature_cols].values
    y_flood = df_eng["flood_label"].values
    y_landslide = df_eng["landslide_label"].values

    print(f"  Total features: {len(all_feature_cols)}")

    # ---- Spatial split (same logic as train_advanced.py) ----
    print("\n[3/4] Reproducing spatial train/test split...")
    spatial_cv = SpatialCV(group_col="state")

    X_train_val, X_test, yf_train_val, yf_test, idx_train_val, idx_test = \
        spatial_cv.get_train_test_split(df_eng, all_feature_cols, "flood_label", test_size=0.20)
    yl_train_val = y_landslide[idx_train_val]
    yl_test = y_landslide[idx_test]

    # Further split train_val -> train + val (same as pipeline)
    df_train_val = df_eng.iloc[idx_train_val].reset_index(drop=True)
    X_train, X_val, yf_train, yf_val, idx_train, idx_val = \
        spatial_cv.get_train_test_split(df_train_val, all_feature_cols, "flood_label", test_size=0.20)
    yl_train = yl_train_val[idx_train]
    yl_val = yl_train_val[idx_val]

    # Scale
    X_train_scaled = feature_engineer.fit_scaler(X_train)
    X_val_scaled = feature_engineer.transform(X_val)
    X_test_scaled = feature_engineer.transform(X_test)

    # Combine train+val for "training set" evaluation (what model saw during fitting + tuning)
    X_trainval_scaled = np.vstack([X_train_scaled, X_val_scaled])
    yf_trainval = np.concatenate([yf_train, yf_val])
    yl_trainval = np.concatenate([yl_train, yl_val])

    print(f"  Train+Val samples: {X_trainval_scaled.shape[0]}  |  Test samples: {X_test_scaled.shape[0]}")
    print(f"  Flood positives  — Train+Val: {yf_trainval.sum()}  |  Test: {yf_test.sum()}")
    print(f"  Landslide positives — Train+Val: {yl_trainval.sum()}  |  Test: {yl_test.sum()}")

    # ---- 2. Load saved models and evaluate ----
    print("\n[4/4] Evaluating models on Training & Testing sets...\n")

    flood_models = {
        "XGBoost (V2)":  "flood_v2_xgb.pkl",
        "LightGBM (V2)": "flood_v2_lgb.pkl",
        "CatBoost (V2)": "flood_v2_cat.pkl",
        "Random Forest (V2)": "flood_v2_rf.pkl",
    }

    landslide_models = {
        "Random Forest (V2)": "landslide_v2_rf.pkl",
        "XGBoost (V2)":       "landslide_v2_xgb.pkl",
        "LightGBM (V2)":      "landslide_v2_lgb.pkl",
    }

    results = {"flood": {}, "landslide": {}}

    # --- Flood ---
    print("=" * 80)
    print("  FLOOD PREDICTION MODELS")
    print("=" * 80)
    print(f"{'Model':<25} {'Train Acc':>10} {'Test Acc':>10} {'Train F1':>10} {'Test F1':>10} {'Test Recall':>12} {'Test AUC':>10}")
    print("-" * 90)

    for name, fname in flood_models.items():
        fpath = MODEL_DIR / fname
        if not fpath.exists():
            print(f"  {name}: model file not found ({fname}), skipping.")
            continue
        model = joblib.load(fpath)
        train_m = evaluate(name, model, X_trainval_scaled, yf_trainval)
        test_m = evaluate(name, model, X_test_scaled, yf_test)
        results["flood"][name] = {"train": train_m, "test": test_m}
        print(f"{name:<25} {train_m['accuracy']:>9.2f}% {test_m['accuracy']:>9.2f}% "
              f"{train_m['f1_score']:>9.2f}% {test_m['f1_score']:>9.2f}% "
              f"{test_m['recall']:>11.2f}% {str(test_m.get('roc_auc','N/A')):>9}%")

    # --- Landslide ---
    print()
    print("=" * 80)
    print("  LANDSLIDE SUSCEPTIBILITY MODELS")
    print("=" * 80)
    print(f"{'Model':<25} {'Train Acc':>10} {'Test Acc':>10} {'Train F1':>10} {'Test F1':>10} {'Test Recall':>12} {'Test AUC':>10}")
    print("-" * 90)

    for name, fname in landslide_models.items():
        fpath = MODEL_DIR / fname
        if not fpath.exists():
            print(f"  {name}: model file not found ({fname}), skipping.")
            continue
        model = joblib.load(fpath)
        train_m = evaluate(name, model, X_trainval_scaled, yl_trainval)
        test_m = evaluate(name, model, X_test_scaled, yl_test)
        results["landslide"][name] = {"train": train_m, "test": test_m}
        print(f"{name:<25} {train_m['accuracy']:>9.2f}% {test_m['accuracy']:>9.2f}% "
              f"{train_m['f1_score']:>9.2f}% {test_m['f1_score']:>9.2f}% "
              f"{test_m['recall']:>11.2f}% {str(test_m.get('roc_auc','N/A')):>9}%")

    print("\n" + "=" * 80)
    print("  Evaluation complete.")
    print("=" * 80)

    # Save results JSON
    out_path = Path(__file__).resolve().parent / "ml" / "results" / "train_vs_test_accuracy.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
