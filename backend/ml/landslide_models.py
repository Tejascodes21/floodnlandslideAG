"""
Landslide Susceptibility Models
=================================
Ensemble of Random Forest, XGBoost, and LightGBM
optimized using Optuna Bayesian Hyperparameter Search.
"""

import numpy as np
import joblib
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import optuna

# Disable optuna verbosity for cleaner stdout
optuna.logging.set_verbosity(optuna.logging.WARNING)

logger = logging.getLogger("geoshield.ml.landslide")
MODEL_DIR = Path(__file__).resolve().parent.parent / "model_dir"


class LandslideModelSuite:
    """
    Refactored landslide susceptibility model suite containing
    Random Forest, XGBoost, and LightGBM.
    Hyperparameters are dynamically tuned using Bayesian optimization (Optuna).
    """
    
    def __init__(self):
        self.models = {}
        # Blending weights matching central config
        self.weights = {"rf": 0.30, "xgb": 0.35, "lgb": 0.35}
        
    def optimize_and_train_rf(self, X_train: np.ndarray, y_train: np.ndarray,
                              X_val: np.ndarray, y_val: np.ndarray) -> RandomForestClassifier:
        logger.info("Optimizing Landslide Random Forest hyperparameters via Optuna...")
        
        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "max_depth": trial.suggest_int("max_depth", 4, 12),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 8),
                "class_weight": trial.suggest_categorical("class_weight", ["balanced", "balanced_subsample", None]),
                "random_state": 42,
                "n_jobs": -1
            }
            model = RandomForestClassifier(**params)
            model.fit(X_train, y_train)
            preds = model.predict(X_val)
            return f1_score(y_val, preds, zero_division=0)
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=10)
        best_params = study.best_params
        best_params["random_state"] = 42
        best_params["n_jobs"] = -1
        
        logger.info(f"Best RF parameters: {best_params} | Best Val F1: {study.best_value:.4f}")
        model = RandomForestClassifier(**best_params)
        model.fit(X_train, y_train)
        self.models["rf"] = model
        return model

    def optimize_and_train_xgb(self, X_train: np.ndarray, y_train: np.ndarray,
                               X_val: np.ndarray, y_val: np.ndarray) -> XGBClassifier:
        logger.info("Optimizing Landslide XGBoost hyperparameters via Optuna...")
        
        n_pos = max(1, np.sum(y_train == 1))
        n_neg = max(1, np.sum(y_train == 0))
        scale_pos = n_neg / n_pos
        
        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "max_depth": trial.suggest_int("max_depth", 3, 8),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1.0, min(10.0, scale_pos)),
                "eval_metric": "logloss",
                "random_state": 42,
                "n_jobs": -1
            }
            model = XGBClassifier(**params)
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
            preds = model.predict(X_val)
            return f1_score(y_val, preds, zero_division=0)
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=10)
        best_params = study.best_params
        best_params["random_state"] = 42
        best_params["n_jobs"] = -1
        best_params["eval_metric"] = "logloss"
        
        logger.info(f"Best XGB parameters: {best_params} | Best Val F1: {study.best_value:.4f}")
        model = XGBClassifier(**best_params)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        self.models["xgb"] = model
        return model

    def optimize_and_train_lgb(self, X_train: np.ndarray, y_train: np.ndarray,
                               X_val: np.ndarray, y_val: np.ndarray) -> LGBMClassifier:
        logger.info("Optimizing Landslide LightGBM hyperparameters via Optuna...")
        
        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "max_depth": trial.suggest_int("max_depth", 3, 8),
                "num_leaves": trial.suggest_int("num_leaves", 15, 63),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "class_weight": trial.suggest_categorical("class_weight", ["balanced", None]),
                "verbosity": -1,
                "random_state": 42,
                "n_jobs": -1
            }
            model = LGBMClassifier(**params)
            model.fit(X_train, y_train)
            preds = model.predict(X_val)
            return f1_score(y_val, preds, zero_division=0)
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=10)
        best_params = study.best_params
        best_params["verbosity"] = -1
        best_params["random_state"] = 42
        best_params["n_jobs"] = -1
        
        logger.info(f"Best LightGBM parameters: {best_params} | Best Val F1: {study.best_value:.4f}")
        model = LGBMClassifier(**best_params)
        model.fit(X_train, y_train)
        self.models["lgb"] = model
        return model
        
    def train_all(self, X_train: np.ndarray, y_train: np.ndarray,
                  X_val: np.ndarray, y_val: np.ndarray):
        """Train all models in the suite."""
        self.optimize_and_train_rf(X_train, y_train, X_val, y_val)
        self.optimize_and_train_xgb(X_train, y_train, X_val, y_val)
        self.optimize_and_train_lgb(X_train, y_train, X_val, y_val)
        logger.info("Landslide model suite training successfully completed.")
        
    def ensemble_predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Computes blended voting probability across RF, XGBoost, LightGBM."""
        probs = np.zeros(X.shape[0])
        total_weight = 0.0
        
        for name, weight in self.weights.items():
            if name in self.models:
                p = self.models[name].predict_proba(X)[:, 1]
                probs += p * weight
                total_weight += weight
                
        if total_weight > 0:
            probs /= total_weight
            
        return probs
        
    def ensemble_predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.ensemble_predict_proba(X) >= threshold).astype(int)
        
    def save_models(self, prefix: str = "landslide_v2"):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        for name, model in self.models.items():
            pkl_path = MODEL_DIR / f"{prefix}_{name}.pkl"
            joblib.dump(model, pkl_path)
            logger.info(f"Saved {name} wrapper model → {pkl_path}")
            
    def load_models(self, prefix: str = "landslide_v2"):
        for name in ["rf", "xgb", "lgb"]:
            pkl_path = MODEL_DIR / f"{prefix}_{name}.pkl"
            if pkl_path.exists():
                self.models[name] = joblib.load(pkl_path)
                logger.info(f"Loaded {name} model ← {pkl_path}")
                
    def get_feature_importance(self, feature_names: List[str]) -> List[Dict]:
        """Averages and ranks feature importance scores from Random Forest, XGBoost and LightGBM."""
        importances = {}
        n_trees = 0
        
        for name in ["rf", "xgb", "lgb"]:
            if name in self.models:
                m = self.models[name]
                if hasattr(m, "estimator"):
                    base_est = getattr(m.estimator, "estimator", m.estimator)
                else:
                    base_est = m
                
                if hasattr(base_est, "feature_importances_"):
                    imp = base_est.feature_importances_
                    for i, f_name in enumerate(feature_names[:len(imp)]):
                        importances[f_name] = importances.get(f_name, 0.0) + imp[i]
                    n_trees += 1
                
        result = []
        for f_name, score in importances.items():
            avg_score = score / max(1, n_trees)
            result.append({
                "feature": f_name,
                "importance": round(float(avg_score), 4),
                "model": "Ensemble (Trees)"
            })
            
        return sorted(result, key=lambda x: -x["importance"])


landslide_model_suite = LandslideModelSuite()
