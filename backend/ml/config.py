"""
Centralized Experiment Configuration
=====================================
Single source of truth for dataset size, splits, seeds, and ensemble weights.

All tunable hyperparameters that affect reproducibility live here so that
experiments can be compared apples-to-apples and reported in the evaluation
report. The training pipeline (ml/train_advanced.py) and inference engine
(ml/inference.py) import these constants instead of hard-coding them.

Everything that does NOT already consume these values keeps working — the
defaults below mirror the historical hard-coded values so behaviour is
unchanged, they are simply now named and documented.
"""

from dataclasses import dataclass, field
from typing import Dict


# --- Global reproducibility -------------------------------------------------
SEED = 42  # used by NumPy, scikit-learn, and model training

# --- Dataset Feature Sets ---------------------------------------------------
BASE_FEATURES = [
    "latitude", "longitude", "elevation", "slope", "ndwi", "ndvi",
    "rain_24h", "rain_72h", "soil_moisture", "river_distance"
]

EXTENDED_FEATURES = [
    "latitude", "longitude", "elevation", "slope", "aspect", "ndvi", "ndwi",
    "mndwi", "evi", "soil_moisture", "rain_24h", "rain_72h", "rain_7d",
    "temperature", "humidity", "river_distance", "drainage_density",
    "flow_accumulation", "historical_events"
]

# --- Train / validation / test split ---------------------------------------
TEST_SIZE = 0.30               # initial holdout (train vs temp)
VAL_FRACTION_OF_TEMP = 0.50    # split the temp holdout into val / test
# => effective split: 70% train / 15% val / 15% test

# --- Ensemble weights (must sum to ~1.0) -----------------------------------
# Flood suite (XGBoost, LightGBM, CatBoost)
FLOOD_ENSEMBLE_WEIGHTS: Dict[str, float] = {
    "xgb": 0.35,
    "lgb": 0.35,
    "cat": 0.30,
}

# Landslide suite (Random Forest, XGBoost, LightGBM)
LANDSLIDE_ENSEMBLE_WEIGHTS: Dict[str, float] = {
    "rf": 0.30,
    "xgb": 0.35,
    "lgb": 0.35,
}

# --- Inference blending (V1 baseline vs V2 advanced) -----------------------
# When both the original (V1) and advanced (V2) models are available, the
# inference engine blends their probabilities. These weights match the
# historical hard-coded blend in ml/inference.py.
INFERENCE_V2_WEIGHT = 0.7
INFERENCE_V1_WEIGHT = 0.3

# --- Decision thresholds (mirrors backend/app/core/config.py) --------------
THRESHOLD_EXTREME = 0.75
THRESHOLD_HIGH = 0.50
THRESHOLD_MODERATE = 0.25


DATASET_SIZE = 500  # Size of historical event dataset
FEATURE_SET = "extended"

@dataclass
class ExperimentConfig:
    """Snapshot of the active experiment configuration for logging/reporting."""

    seed: int = SEED
    dataset_size: int = DATASET_SIZE
    feature_set: str = FEATURE_SET
    test_size: float = TEST_SIZE
    val_fraction_of_temp: float = VAL_FRACTION_OF_TEMP
    flood_ensemble_weights: Dict[str, float] = field(
        default_factory=lambda: dict(FLOOD_ENSEMBLE_WEIGHTS)
    )
    landslide_ensemble_weights: Dict[str, float] = field(
        default_factory=lambda: dict(LANDSLIDE_ENSEMBLE_WEIGHTS)
    )

    def as_dict(self) -> dict:
        return {
            "seed": self.seed,
            "dataset_size": self.dataset_size,
            "feature_set": self.feature_set,
            "split": {
                "test_size": self.test_size,
                "val_fraction_of_temp": self.val_fraction_of_temp,
            },
            "flood_ensemble_weights": self.flood_ensemble_weights,
            "landslide_ensemble_weights": self.landslide_ensemble_weights,
            "thresholds": {
                "extreme": THRESHOLD_EXTREME,
                "high": THRESHOLD_HIGH,
                "moderate": THRESHOLD_MODERATE,
            },
        }


# Active configuration singleton
config = ExperimentConfig()
