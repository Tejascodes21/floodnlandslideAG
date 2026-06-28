#!/usr/bin/env python
"""
Model Evaluation Report Generator
==================================
Reads the persisted evaluation JSON produced by train_advanced.py and emits a
human-readable Markdown report covering per-model metrics, confusion matrices,
feature-importance rankings, and ROC data.

This is the academic deliverable — run it after training to refresh the report:

    cd backend && python -m ml.generate_report

The report is written to <repo>/docs/ML_EVALUATION.md so it sits at the project
root alongside the rest of the documentation.
"""

import json
from pathlib import Path
from datetime import datetime

ML_DIR = Path(__file__).resolve().parent
RESULTS_PATH = ML_DIR / "results" / "advanced_evaluation_v2.json"
# repo root = backend/../  -> docs/ lives next to backend/
DOCS_DIR = ML_DIR.parent.parent / "docs"
REPORT_PATH = DOCS_DIR / "ML_EVALUATION.md"

# Display-friendly metric labels in column order
METRIC_KEYS = [
    ("accuracy", "Accuracy"),
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("f1_score", "F1 Score"),
    ("roc_auc", "ROC-AUC"),
    ("pr_auc", "PR-AUC"),
    ("brier_score", "Brier Score"),
    ("specificity", "Specificity"),
    ("npv", "NPV"),
]

MODEL_LABELS = {
    "rf": "Random Forest",
    "xgb": "XGBoost",
    "lgb": "LightGBM",
    "cat": "CatBoost",
    "lstm": "LSTM",
    "cnn": "CNN",
    "cnn_lstm": "CNN-LSTM",
    "ensemble": "Ensemble",
}


def _pct(x):
    """Render a percentage-style metric."""
    try:
        return f"{float(x):.2f}%"
    except (TypeError, ValueError):
        return "—"


def _dec(x):
    """Render a decimal-style metric (Brier score)."""
    try:
        return f"{float(x):.4f}"
    except (TypeError, ValueError):
        return "—"


def render_metrics_table(models: dict) -> str:
    """Render a markdown table of all metrics for one hazard's model suite."""
    header = "| Model | " + " | ".join(label for _, label in METRIC_KEYS) + " |"
    sep = "|---" * (len(METRIC_KEYS) + 1) + "|"
    lines = [header, sep]
    for key in ["rf", "xgb", "lgb", "cat", "ensemble"]:
        m = models.get(key)
        if not m:
            continue
        label = MODEL_LABELS.get(key, key)
        cells = [label]
        for field, _ in METRIC_KEYS:
            val = m.get(field)
            if field == "brier_score":
                cells.append(_dec(val))
            else:
                cells.append(_pct(val))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_confusion_matrix(name: str, m: dict) -> str:
    """Render a single model's confusion matrix as a small markdown table."""
    cm = m.get("confusion_matrix", {})
    if not cm:
        return ""
    tn, fp = cm.get("tn", 0), cm.get("fp", 0)
    fn, tp = cm.get("fn", 0), cm.get("tp", 0)
    label = MODEL_LABELS.get(name, name)
    return (
        f"**{label}**\n\n"
        f"| | Predicted Negative | Predicted Positive |\n"
        f"|---|---|---|\n"
        f"| **Actual Negative** | {tn} | {fp} |\n"
        f"| **Actual Positive** | {fn} | {tp} |\n"
    )


def render_feature_importance(importances: list, top_n: int = 15) -> str:
    """Aggregate per-feature importance across models and rank the top N."""
    if not importances:
        return "_No feature-importance data available._"

    agg = {}
    for entry in importances:
        feat = entry.get("feature")
        if not feat:
            continue
        agg.setdefault(feat, []).append(float(entry.get("importance", 0.0)))

    # average importance across the models that reported the feature
    ranked = sorted(
        ((feat, sum(vals) / len(vals)) for feat, vals in agg.items()),
        key=lambda kv: kv[1],
        reverse=True,
    )[:top_n]

    lines = ["| Rank | Feature | Mean Importance |", "|---|---|---|"]
    for i, (feat, imp) in enumerate(ranked, 1):
        bar = "█" * max(1, int(imp * 100))
        lines.append(f"| {i} | `{feat}` | {imp:.4f} {bar} |")
    return "\n".join(lines)


def generate() -> str:
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Evaluation results not found at {RESULTS_PATH}. "
            "Run `python -m ml.train_advanced` first."
        )

    with open(RESULTS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    ds = data.get("dataset", {})
    flood = data.get("flood_models", {})
    slide = data.get("landslide_models", {})
    flood_imp = data.get("flood_feature_importance", [])
    slide_imp = data.get("landslide_feature_importance", [])
    roc = data.get("roc_data", {})
    cv = data.get("cross_validation", {})

    sections = []
    sections.append("# GeoShield AI — Model Evaluation Report\n")
    sections.append(
        f"_Generated automatically by `ml/generate_report.py` on "
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}._\n"
    )

    # Dataset summary
    sections.append("## 1. Dataset\n")
    n = ds.get("n_samples", "—")
    nf = ds.get("n_features", "—")
    feats = ds.get("features", [])
    sections.append(
        f"- **Samples:** {n}\n- **Engineered features:** {nf}\n"
    )
    if feats:
        sections.append(
            "- **Feature columns:**\n\n"
            + ", ".join(f"`{f}`" for f in feats)
            + "\n"
        )

    # Methodology note
    sections.append(
        "## 2. Methodology\n\n"
        "Models are trained on a real-data geospatial machine learning pipeline (compiled by "
        "`ml/data_ingestion.py`) that integrates historical flood and landslide occurrence coordinates in India "
        "with terrain indicators (SRTM DEM), satellite indices (Sentinel-1 & Sentinel-2), and precipitation data "
        "from IMD / Open-Meteo weather history. Negative control coordinates (no hazard) are sampled to establish baseline classes.\n\n"
        "To prevent spatial data leakage, training and testing splits are partitioned using Spatial Cross-Validation "
        "(`SpatialCV` GroupKFold by state/region) ensuring no overlapping districts. Ensembles are constructed via "
        "weighted soft-voting. Tree-based models (Random Forest, XGBoost, LightGBM, CatBoost) are optimized "
        "via Optuna Bayesian hyperparameter search. Models are audited for potential target/feature leakage.\n"
    )

    # Flood results
    sections.append("## 3. Flood Prediction Models\n")
    sections.append("### 3.1 Metrics\n")
    sections.append(render_metrics_table(flood) + "\n")
    sections.append("### 3.2 Confusion Matrices\n")
    for name in ["xgb", "lgb", "cat", "ensemble"]:
        cm_md = render_confusion_matrix(name, flood.get(name, {}))
        if cm_md:
            sections.append(cm_md)

    # Landslide results
    sections.append("## 4. Landslide Prediction Models\n")
    sections.append("### 4.1 Metrics\n")
    sections.append(render_metrics_table(slide) + "\n")
    sections.append("### 4.2 Confusion Matrices\n")
    for name in ["rf", "xgb", "lgb", "ensemble"]:
        cm_md = render_confusion_matrix(name, slide.get(name, {}))
        if cm_md:
            sections.append(cm_md)

    # Feature importance
    sections.append("## 5. Feature Importance\n")
    sections.append("### 5.1 Flood drivers (top 15)\n")
    sections.append(render_feature_importance(flood_imp) + "\n")
    sections.append("### 5.2 Landslide drivers (top 15)\n")
    sections.append(render_feature_importance(slide_imp) + "\n")

    # Cross-validation if present
    if cv:
        sections.append("## 6. Cross-Validation\n")
        sections.append(
            "| Hazard | Model | Mean F1 | Std F1 |\n|---|---|---|---|"
        )
        for hazard_key, models_cv in cv.items():
            for model_name, stats in models_cv.items():
                mean = stats.get("f1_mean", stats.get("mean", "—"))
                std = stats.get("f1_std", stats.get("std", "—"))
                sections.append(
                    f"| {hazard_key} | {MODEL_LABELS.get(model_name, model_name)} "
                    f"| {mean} | {std} |"
                )
        sections.append("")

    # ROC data reference
    if roc:
        sections.append(
            "## 7. ROC Curve Data\n\n"
            "ROC curve coordinates for each model are stored in the source JSON "
            "under the `roc_data` key and are exposed to the frontend via the "
            "`/api/predict/models/comparison` endpoint for interactive charting.\n"
        )

    sections.append(
        "## 8. Reproducibility\n\n"
        "All randomness is seeded (dataset generation seed = 42, NumPy / PyTorch "
        "/ scikit-learn seeds pinned in `ml/train_advanced.py`). Re-running "
        "`python -m ml.train_advanced` reproduces the metrics above within "
        "floating-point tolerance. Hyperparameters are centralised in "
        "`ml/config.py`.\n"
    )

    return "\n".join(sections)


def main():
    report = generate()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Evaluation report written to {REPORT_PATH}")
    print(f"  ({len(report)} characters)")


if __name__ == "__main__":
    main()
