"""
Flood Risk Prediction Models
==============================
Gradient Boosted Tree Ensembles (XGBoost, LightGBM, CatBoost)
with Optuna Bayesian Hyperparameter Optimization.
"""

import numpy as np
import joblib
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from sklearn.metrics import f1_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
import optuna

# Disable optuna verbosity for cleaner stdout
optuna.logging.set_verbosity(optuna.logging.WARNING)

logger = logging.getLogger("geoshield.ml.flood")
MODEL_DIR = Path(__file__).resolve().parent.parent / "model_dir"


class FloodModelSuite:
    """
    Refactored flood prediction suite containing XGBoost, LightGBM, and CatBoost.
    Uses Bayesian optimization via Optuna to determine hyperparameter configurations.
    """
    
    def __init__(self):
        self.models = {}
        # Blending weights matching central config
        self.weights = {"xgb": 0.35, "lgb": 0.35, "cat": 0.30}
        
    def optimize_and_train_xgb(self, X_train: np.ndarray, y_train: np.ndarray,
                               X_val: np.ndarray, y_val: np.ndarray) -> XGBClassifier:
        logger.info("Optimizing Flood XGBoost hyperparameters via Optuna...")
        
        # Calculate class scale weight
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
        logger.info("Optimizing Flood LightGBM hyperparameters via Optuna...")
        
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

    def optimize_and_train_cat(self, X_train: np.ndarray, y_train: np.ndarray,
                               X_val: np.ndarray, y_val: np.ndarray) -> CatBoostClassifier:
        logger.info("Optimizing Flood CatBoost hyperparameters via Optuna...")
        
        def objective(trial):
            params = {
                "iterations": trial.suggest_int("iterations", 50, 200),
                "depth": trial.suggest_int("depth", 3, 8),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
                "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
                "verbose": False,
                "random_seed": 42
            }
            model = CatBoostClassifier(**params)
            model.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=False)
            preds = model.predict(X_val)
            return f1_score(y_val, preds, zero_division=0)
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=10)
        best_params = study.best_params
        best_params["verbose"] = False
        best_params["random_seed"] = 42
        
        logger.info(f"Best CatBoost parameters: {best_params} | Best Val F1: {study.best_value:.4f}")
        model = CatBoostClassifier(**best_params)
        model.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=False)
        self.models["cat"] = model
        return model
        
    def train_all(self, X_train: np.ndarray, y_train: np.ndarray,
                  X_val: np.ndarray, y_val: np.ndarray):
        """Train all models in the suite."""
        self.optimize_and_train_xgb(X_train, y_train, X_val, y_val)
        self.optimize_and_train_lgb(X_train, y_train, X_val, y_val)
        self.optimize_and_train_cat(X_train, y_train, X_val, y_val)
        logger.info("Flood model suite training successfully completed.")
        
    def ensemble_predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Computes blended voting probability across XGB, LightGBM, CatBoost."""
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
        
    def save_models(self, prefix: str = "flood_v2"):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        for name, model in self.models.items():
            pkl_path = MODEL_DIR / f"{prefix}_{name}.pkl"
            joblib.dump(model, pkl_path)
            logger.info(f"Saved {name} wrapper model → {pkl_path}")
            
    def load_models(self, prefix: str = "flood_v2"):
        for name in ["xgb", "lgb", "cat"]:
            pkl_path = MODEL_DIR / f"{prefix}_{name}.pkl"
            if pkl_path.exists():
                self.models[name] = joblib.load(pkl_path)
                logger.info(f"Loaded {name} model ← {pkl_path}")
                
    def get_feature_importance(self, feature_names: List[str]) -> List[Dict]:
        """Averages and ranks feature importance scores from XGBoost and LightGBM."""
        importances = {}
        n_trees = 0
        
        for name in ["xgb", "lgb"]:
            if name in self.models:
                imp = self.models[name].feature_importances_
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


flood_model_suite = FloodModelSuite()
