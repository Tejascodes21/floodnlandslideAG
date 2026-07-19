"""
Model Evaluation Pipeline
===========================
Comprehensive evaluation metrics, cross-validation, calibration,
and model comparison analysis for flood and landslide prediction.
"""

import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    average_precision_score, brier_score_loss, log_loss,
    balanced_accuracy_score, matthews_corrcoef, cohen_kappa_score
)
from sklearn.model_selection import StratifiedKFold

logger = logging.getLogger("geoshield.ml.evaluation")
RESULTS_DIR = Path(__file__).parent / "results"


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10):
    """
    Computes Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).
    """
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
    return float(ece), float(mce)


def mcnemar_test(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray):
    """
    Performs McNemar's statistical significance test between two models.
    """
    a_correct = (y_pred_a == y_true)
    b_correct = (y_pred_b == y_true)
    
    n01 = np.sum(a_correct & ~b_correct)
    n10 = np.sum(~a_correct & b_correct)
    
    if n01 + n10 == 0:
        stat = 0.0
        pval = 1.0
    else:
        # Edwards' continuity correction
        stat = (abs(n01 - n10) - 1.0) ** 2 / (n01 + n10)
        try:
            from scipy.stats import chi2
            pval = chi2.sf(stat, df=1)
        except ImportError:
            # Fallback normal approximation if scipy is not installed
            from math import erf, sqrt
            z = abs(n01 - n10) / sqrt(n01 + n10)
            pval = 1.0 - erf(z / sqrt(2.0))
            
    return float(stat), float(pval)


class ModelEvaluator:
    """Comprehensive evaluation pipeline for binary classification models."""
    
    def __init__(self):
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def evaluate_model(self, y_true: np.ndarray, y_pred: np.ndarray,
                       y_proba: np.ndarray = None,
                       model_name: str = "Model") -> Dict:
        """
        Compute comprehensive classification metrics.
        """
        metrics = {
            "model": model_name,
            "accuracy": round(accuracy_score(y_true, y_pred) * 100, 2),
            "precision": round(precision_score(y_true, y_pred, zero_division=0) * 100, 2),
            "recall": round(recall_score(y_true, y_pred, zero_division=0) * 100, 2),
            "f1_score": round(f1_score(y_true, y_pred, zero_division=0) * 100, 2),
            "balanced_accuracy": round(balanced_accuracy_score(y_true, y_pred) * 100, 2),
            "mcc": round(matthews_corrcoef(y_true, y_pred), 4),
            "cohen_kappa": round(cohen_kappa_score(y_true, y_pred), 4)
        }
        
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp = cm[0, 0], cm[0, 1]
        fn, tp = cm[1, 0], cm[1, 1]
        
        metrics["confusion_matrix"] = {
            "tn": int(tn), "fp": int(fp),
            "fn": int(fn), "tp": int(tp)
        }
        
        metrics["specificity"] = round(tn / max(tn + fp, 1) * 100, 2)
        metrics["npv"] = round(tn / max(tn + fn, 1) * 100, 2)
        
        if y_proba is not None:
            try:
                metrics["roc_auc"] = round(roc_auc_score(y_true, y_proba) * 100, 2)
            except ValueError:
                metrics["roc_auc"] = 0.0
            
            try:
                metrics["pr_auc"] = round(average_precision_score(y_true, y_proba) * 100, 2)
            except ValueError:
                metrics["pr_auc"] = 0.0
            
            try:
                metrics["log_loss"] = round(log_loss(y_true, y_proba), 4)
            except ValueError:
                metrics["log_loss"] = None
            
            metrics["brier_score"] = round(brier_score_loss(y_true, y_proba), 4)
            ece, mce = expected_calibration_error(y_true, y_proba)
            metrics["ece"] = round(ece, 4)
            metrics["mce"] = round(mce, 4)
        
        return metrics
    
    def evaluate_suite(self, models: Dict, X_test: np.ndarray,
                       y_test: np.ndarray, hazard_type: str = "flood") -> Dict:
        """Evaluate all models in a suite and generate comparison."""
        results = {}
        
        for name, model in models.items():
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
            
            metrics = self.evaluate_model(y_test, y_pred, y_proba, model_name=f"{hazard_type}_{name}")
            results[name] = metrics
            
            logger.info(f"[{hazard_type.upper()} {name}] Acc={metrics['accuracy']}% "
                         f"F1={metrics['f1_score']}% AUC={metrics.get('roc_auc', 'N/A')}%")
        
        return results
    
    def cross_validate(self, model, X: np.ndarray, y: np.ndarray,
                       n_folds: int = 5, model_name: str = "Model") -> Dict:
        """Stratified K-fold cross-validation."""
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
        
        fold_metrics = {"accuracy": [], "f1": [], "precision": [], "recall": []}
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            X_tr, X_val = X[train_idx], X[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]
            
            from sklearn.base import clone
            try:
                m = clone(model)
                m.fit(X_tr, y_tr)
                y_pred = m.predict(X_val)
            except Exception:
                continue
            
            fold_metrics["accuracy"].append(accuracy_score(y_val, y_pred))
            fold_metrics["f1"].append(f1_score(y_val, y_pred, zero_division=0))
            fold_metrics["precision"].append(precision_score(y_val, y_pred, zero_division=0))
            fold_metrics["recall"].append(recall_score(y_val, y_pred, zero_division=0))
        
        return {
            "model": model_name,
            "n_folds": n_folds,
            "mean_accuracy": round(np.mean(fold_metrics["accuracy"]) * 100, 2),
            "std_accuracy": round(np.std(fold_metrics["accuracy"]) * 100, 2),
            "mean_f1": round(np.mean(fold_metrics["f1"]) * 100, 2),
            "std_f1": round(np.std(fold_metrics["f1"]) * 100, 2),
            "mean_precision": round(np.mean(fold_metrics["precision"]) * 100, 2),
            "mean_recall": round(np.mean(fold_metrics["recall"]) * 100, 2),
        }
    
    def generate_roc_data(self, y_true: np.ndarray, y_proba: np.ndarray,
                           n_points: int = 50) -> List[Dict]:
        """Generate ROC curve data points for frontend visualization."""
        thresholds = np.linspace(0, 1, n_points)
        points = []
        
        for t in thresholds:
            y_pred = (y_proba >= t).astype(int)
            cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
            
            tn, fp = cm[0, 0], cm[0, 1]
            fn, tp = cm[1, 0], cm[1, 1]
            
            fpr = fp / max(fp + tn, 1)
            tpr = tp / max(tp + fn, 1)
            
            points.append({"threshold": round(float(t), 3), "fpr": round(fpr, 4), "tpr": round(tpr, 4)})
        
        return points
    
    def save_results(self, results: Dict, filename: str = "evaluation_results.json"):
        filepath = RESULTS_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Evaluation results saved to {filepath}")
        return str(filepath)


evaluator = ModelEvaluator()
