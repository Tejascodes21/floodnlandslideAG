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
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("geoshield.ml.features")

FEATURE_LIST_40 = [
    "latitude", "longitude", "elevation", "slope", "aspect", "terrain_roughness", "curvature", "twi", 
    "ndwi", "ndvi", "mndwi", "evi", "rain_24h", "rain_48h", "rain_72h", "rain_7d", "spi", "soil_moisture", 
    "sar_backscatter", "sar_vh", "drainage_density", "river_proximity", "water_occurrence", "flow_accumulation", 
    "soil_type_encoded", "historical_flood_freq", "rain_intensity_24_72", "rain_intensity_48_7d", "flood_compound", 
    "landslide_compound", "slope_moisture_interaction", "rain_elevation_interaction", "vegetation_vulnerability", 
    "water_saturation_index", "log_rain_24h", "log_rain_72h", "log_elevation", "log_flow_acc", "slope_squared", 
    "rain_24h_squared"
]

class FeatureEngineer:
    """
    Advanced feature engineering for hazard prediction models.
    
    Transforms raw geospatial features into model-ready representations
    using continuous physical interactions (no deterministic thresholds).
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.fitted = False
    
    def get_feature_names(self) -> List[str]:
        return FEATURE_LIST_40

    def get_engineered_feature_names(self) -> List[str]:
        # For backward compatibility
        from ml.config import EXTENDED_FEATURES
        return [f for f in FEATURE_LIST_40 if f not in EXTENDED_FEATURES]

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies all feature engineering transformations.
        Produces exactly the 40-feature set in the required order.
        """
        df = df.copy()
        
        # Make sure river_proximity exists (mapping from river_distance)
        if 'river_proximity' not in df.columns and 'river_distance' in df.columns:
            df['river_proximity'] = df['river_distance']
            
        # Generate missing core inputs if not present
        if 'aspect' not in df.columns:
            df['aspect'] = 180.0
        if 'terrain_roughness' not in df.columns:
            df['terrain_roughness'] = 5.0
        if 'curvature' not in df.columns:
            df['curvature'] = 0.0
        if 'twi' not in df.columns:
            df['twi'] = 10.0
        if 'mndwi' not in df.columns:
            df['mndwi'] = df['ndwi'] * 0.82
        if 'evi' not in df.columns:
            df['evi'] = df['ndvi'] * 0.78
        if 'rain_48h' not in df.columns:
            df['rain_48h'] = (df['rain_24h'] + df['rain_72h']) / 2.0
        if 'spi' not in df.columns:
            df['spi'] = 0.0
        if 'sar_backscatter' not in df.columns:
            df['sar_backscatter'] = np.where(df['ndwi'] > 0.1, -20.0, -12.0)
        if 'sar_vh' not in df.columns:
            df['sar_vh'] = df['sar_backscatter'] - 6.0
        if 'water_occurrence' not in df.columns:
            df['water_occurrence'] = 50.0 + df['ndwi'] * 50.0
        if 'soil_type_encoded' not in df.columns:
            df['soil_type_encoded'] = np.where(df['elevation'] > 1000, 2, np.where(df['slope'] > 15, 1, 0))
        if 'historical_flood_freq' not in df.columns:
            df['historical_flood_freq'] = df['historical_events']
            
        # Derived interactions
        df['rain_intensity_24_72'] = np.where(df['rain_72h'] > 0, df['rain_24h'] / df['rain_72h'], 0.0)
        df['rain_intensity_48_7d'] = np.where(df['rain_7d'] > 0, df['rain_48h'] / df['rain_7d'], 0.0)
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

        # Retain original columns (like labels, state, district, date) but ensure engineered columns exist
        for col in FEATURE_LIST_40:
            if col not in df.columns:
                df[col] = 0.0

        # Sort the output DataFrame to match the exact expected 40 features order
        extra_cols = [c for c in df.columns if c not in FEATURE_LIST_40]
        return df[FEATURE_LIST_40 + extra_cols]
    
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
        
        # Map river_distance to river_proximity if needed
        if 'river_proximity' not in f and 'river_distance' in f:
            f['river_proximity'] = f['river_distance']
            
        rain_24h = float(f.get("rain_24h", 0.0))
        rain_72h = float(f.get("rain_72h", 0.0))
        rain_7d = float(f.get("rain_7d", rain_72h * 1.5))
        rain_48h = (rain_24h + rain_72h) / 2.0
        
        slope = float(f.get("slope", 5.0))
        elevation = float(f.get("elevation", 100.0))
        ndvi = float(f.get("ndvi", 0.5))
        ndwi = float(f.get("ndwi", 0.0))
        soil_moisture = float(f.get("soil_moisture", 50.0))
        aspect = float(f.get("aspect", 180.0))
        roughness = float(f.get("terrain_roughness", 5.0))
        curvature = float(f.get("curvature", 0.0))
        twi = float(f.get("twi", 10.0))
        mndwi = float(f.get("mndwi", ndwi * 0.82))
        evi = float(f.get("evi", ndvi * 0.78))
        spi = float(f.get("spi", 0.0))
        
        sar_back = float(f.get("sar_backscatter", -20.0 if ndwi > 0.1 else -12.0))
        sar_vh = float(f.get("sar_vh", sar_back - 6.0))
        water_occur = float(f.get("water_occurrence", 50.0 + ndwi * 50.0))
        soil_type = int(f.get("soil_type_encoded", 2 if elevation > 1000 else (1 if slope > 15 else 0)))
        hist_events = float(f.get("historical_events", 0.0))
        hist_flood_freq = float(f.get("historical_flood_freq", hist_events))
        river_prox = float(f.get("river_proximity", 2.0))
        flow_acc = float(f.get("flow_accumulation", 100.0))

        # Fill base features
        f["aspect"] = aspect
        f["terrain_roughness"] = roughness
        f["curvature"] = curvature
        f["twi"] = twi
        f["mndwi"] = mndwi
        f["evi"] = evi
        f["rain_48h"] = rain_48h
        f["spi"] = spi
        f["sar_backscatter"] = sar_back
        f["sar_vh"] = sar_vh
        f["water_occurrence"] = water_occur
        f["soil_type_encoded"] = soil_type
        f["historical_flood_freq"] = hist_flood_freq
        f["river_proximity"] = river_prox
        
        # Interactions
        f["rain_intensity_24_72"] = rain_24h / max(rain_72h, 0.01)
        f["rain_intensity_48_7d"] = rain_48h / max(rain_7d, 0.01)
        f["flood_compound"] = rain_24h * (1.0 - elevation / 2500.0)
        f["landslide_compound"] = slope * rain_72h * (1.0 - ndvi)
        f["slope_moisture_interaction"] = slope * soil_moisture
        f["rain_elevation_interaction"] = rain_72h * elevation
        f["vegetation_vulnerability"] = (1.0 - ndvi) * slope
        f["water_saturation_index"] = soil_moisture * ndwi
        
        # Log transforms
        f["log_rain_24h"] = np.log1p(rain_24h)
        f["log_rain_72h"] = np.log1p(rain_72h)
        f["log_elevation"] = np.log1p(elevation)
        f["log_flow_acc"] = np.log1p(flow_acc)
        
        # Squared terms
        f["slope_squared"] = slope ** 2
        f["rain_24h_squared"] = rain_24h ** 2
        
        return f


feature_engineer = FeatureEngineer()
