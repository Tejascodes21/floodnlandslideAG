"""
Feature Engineering Pipeline
==============================
Derives additional features through polynomial interactions,
temporal aggregations, and domain-specific transformations.
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict
from sklearn.preprocessing import StandardScaler, PolynomialFeatures

logger = logging.getLogger("geoshield.ml.features")


class FeatureEngineer:
    """
    Advanced feature engineering for hazard prediction models.
    
    Transforms raw geospatial features into model-ready representations
    using continuous physical interactions (no deterministic thresholds).
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.fitted = False
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies all feature engineering transformations.
        
        Adds derived columns:
          - Slope-rainfall interaction (critical for landslides)
          - Soil saturation index
          - Vegetation degradation index
          - Terrain instability score
          - Rainfall accumulation
          - River proximity factor
          - Upstream catchment indicator
          - Rain intensity ratios
          - Log-transformed heavy-tail features
        """
        df = df.copy()
        
        # 1. Slope-Rainfall Interaction (landslide driver)
        df["slope_rainfall_interaction"] = df["slope"] * df["rain_72h"]
        
        # 2. Soil Saturation Index (combining soil moisture and recent precipitation)
        df["soil_saturation_index"] = df["soil_moisture"] * df["rain_72h"]
        
        # 3. Vegetation Degradation Index (bare/depleted soil vulnerability)
        df["vegetation_degradation_index"] = (1.0 - df["ndvi"]) * df["rain_24h"]
        
        # 4. Terrain Instability Score
        df["terrain_instability_score"] = df["slope"] * df.get("terrain_roughness", 5.0) / (df["ndvi"] + 0.1)
        
        # 5. Rainfall Accumulation (total temporal rainfall weight)
        df["rainfall_accumulation"] = df["rain_24h"] + df["rain_72h"] + df.get("rain_7d", df["rain_72h"] * 1.5)
        
        # 6. River Proximity Factor (closer to river = higher risk; inverse distance)
        river_dist = df.get("river_distance", df.get("river_proximity", 2.0))
        df["river_proximity_factor"] = 1.0 / (river_dist + 0.1)
        
        # 7. Upstream Catchment Indicator
        df["upstream_catchment_indicator"] = df.get("flow_accumulation", 100.0) * df["rain_72h"]
        
        # 8. Rainfall intensity ratios
        df["rain_intensity_24_72"] = np.where(
            df["rain_72h"] > 0, df["rain_24h"] / df["rain_72h"], 0
        )
        
        # --- Log transforms for heavy-tailed distributions ---
        df["log_rain_24h"] = np.log1p(df["rain_24h"])
        df["log_rain_72h"] = np.log1p(df["rain_72h"])
        df["log_elevation"] = np.log1p(df["elevation"])
        df["log_flow_acc"] = np.log1p(df.get("flow_accumulation", 100.0))
        
        return df
    
    def get_engineered_feature_names(self) -> List[str]:
        """Returns the list of all engineered feature names."""
        return [
            "slope_rainfall_interaction", "soil_saturation_index",
            "vegetation_degradation_index", "terrain_instability_score",
            "rainfall_accumulation", "river_proximity_factor",
            "upstream_catchment_indicator", "rain_intensity_24_72",
            "log_rain_24h", "log_rain_72h", "log_elevation", "log_flow_acc"
        ]
    
    def fit_scaler(self, X: np.ndarray) -> np.ndarray:
        """Fit and transform the scaler."""
        self.fitted = True
        return self.scaler.fit_transform(X)
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform using fitted scaler."""
        if not self.fitted:
            return self.scaler.fit_transform(X)
        return self.scaler.transform(X)
    
    def engineer_single_sample(self, features: Dict) -> Dict:
        """
        Apply feature engineering to a single sample dictionary.
        Used during inference.
        """
        f = features.copy()
        
        rain_24h = f.get("rain_24h", 0.0)
        rain_72h = f.get("rain_72h", 0.0)
        rain_7d = f.get("rain_7d", rain_72h * 1.5)
        slope = f.get("slope", 5.0)
        ndvi = f.get("ndvi", 0.5)
        soil_moisture = f.get("soil_moisture", 50.0)
        roughness = f.get("terrain_roughness", 5.0)
        river_dist = f.get("river_distance", f.get("river_proximity", 2.0))
        flow_acc = f.get("flow_accumulation", 100.0)
        
        f["slope_rainfall_interaction"] = slope * rain_72h
        f["soil_saturation_index"] = soil_moisture * rain_72h
        f["vegetation_degradation_index"] = (1.0 - ndvi) * rain_24h
        f["terrain_instability_score"] = slope * roughness / (ndvi + 0.1)
        f["rainfall_accumulation"] = rain_24h + rain_72h + rain_7d
        f["river_proximity_factor"] = 1.0 / (river_dist + 0.1)
        f["upstream_catchment_indicator"] = flow_acc * rain_72h
        f["rain_intensity_24_72"] = rain_24h / max(rain_72h, 0.01)
        
        f["log_rain_24h"] = np.log1p(rain_24h)
        f["log_rain_72h"] = np.log1p(rain_72h)
        f["log_elevation"] = np.log1p(f.get("elevation", 100.0))
        f["log_flow_acc"] = np.log1p(flow_acc)
        
        return f


feature_engineer = FeatureEngineer()
