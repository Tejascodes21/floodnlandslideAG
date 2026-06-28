"""
Production Inference Engine
=============================
Loads all trained models, orchestrates ensemble predictions,
and returns structured prediction responses with confidence
intervals and SHAP explanations.
"""

import numpy as np
import joblib
import logging
import time
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("geoshield.ml.inference")
MODEL_DIR = Path(__file__).parent.parent / "model_dir"


class MultiHazardInferenceEngine:
    """
    Production inference engine for multi-hazard prediction.
    
    Loads both v1 (original) and v2 (advanced) models,
    runs ensemble predictions, and generates comprehensive results.
    """
    
    def __init__(self):
        self.v1_models = {}
        self.v2_flood = None
        self.v2_landslide = None
        self.scaler = None
        self.feature_cols = None
        self.ready = False
        self._load_models()
    
    def _load_models(self):
        """Load all available models from model_dir."""
        try:
            # V1 models (original train_pipeline.py)
            if (MODEL_DIR / "scaler.pkl").exists():
                self.scaler = joblib.load(MODEL_DIR / "scaler.pkl")
                self.feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
                self.v1_models["xgb_flood"] = joblib.load(MODEL_DIR / "xgb_flood.pkl")
                self.v1_models["rf_landslide"] = joblib.load(MODEL_DIR / "rf_landslide.pkl")
                logger.info("V1 models loaded successfully.")
            
            # V2 models (advanced suite)
            try:
                from .flood_models import FloodModelSuite
                from .landslide_models import LandslideModelSuite
                
                self.v2_flood = FloodModelSuite()
                self.v2_flood.load_models("flood_v2")
                
                self.v2_landslide = LandslideModelSuite()
                self.v2_landslide.load_models("landslide_v2")
                
                if (MODEL_DIR / "scaler_v2.pkl").exists():
                    self.scaler_v2 = joblib.load(MODEL_DIR / "scaler_v2.pkl")
                if (MODEL_DIR / "feature_cols_v2.pkl").exists():
                    self.feature_cols_v2 = joblib.load(MODEL_DIR / "feature_cols_v2.pkl")
                
                if self.v2_flood.models:
                    logger.info(f"V2 flood models loaded: {list(self.v2_flood.models.keys())}")
                if self.v2_landslide.models:
                    logger.info(f"V2 landslide models loaded: {list(self.v2_landslide.models.keys())}")
            except Exception as e:
                logger.debug(f"V2 models not yet trained: {e}")
            
            self.ready = bool(self.v1_models or (self.v2_flood and self.v2_flood.models))
            
        except Exception as e:
            logger.warning(f"Model loading failed: {e}. Run training pipeline first.")
            self.ready = False
    
    def predict(self, features: Dict, lang: str = "en") -> Dict:
        """
        Run multi-hazard prediction from a feature dictionary.
        
        Parameters:
            features: Dict with keys matching feature columns
            lang: Language code for explanations (en, hi, mr)
            
        Returns:
            Comprehensive prediction result with probabilities,
            severity, confidence, and SHAP explanations
        """
        start_time = time.time()
        
        if not self.ready:
            return {"error": "Models not loaded. Run training pipeline.", "ready": False}
        
        # Build feature vector for V1 models
        v1_result = self._predict_v1(features)
        
        # Build feature vector for V2 models
        v2_result = self._predict_v2(features)
        
        # Merge results (prefer V2 if available, else use V1)
        if v2_result:
            flood_prob = v2_result["flood_prob"] * 0.6 + v1_result["flood_prob"] * 0.4
            landslide_prob = v2_result["landslide_prob"] * 0.6 + v1_result["landslide_prob"] * 0.4
        else:
            flood_prob = v1_result["flood_prob"]
            landslide_prob = v1_result["landslide_prob"]
        
        # Confidence intervals (based on model agreement)
        flood_ci = self._compute_confidence_interval(v1_result, v2_result, "flood")
        landslide_ci = self._compute_confidence_interval(v1_result, v2_result, "landslide")
        
        # Severity classification
        flood_severity = self._classify_severity(flood_prob)
        landslide_severity = self._classify_severity(landslide_prob)
        
        # SHAP explanation
        shap_data = self._generate_explanation(features, flood_prob, landslide_prob, lang)
        
        processing_ms = round((time.time() - start_time) * 1000, 1)
        
        return {
            "flood": {
                "probability": round(flood_prob, 4),
                "percentage": round(flood_prob * 100, 1),
                "severity": flood_severity,
                "confidence_interval": flood_ci,
                "models_used": v1_result.get("flood_models", []) + v2_result.get("flood_models", []) if v2_result else v1_result.get("flood_models", [])
            },
            "landslide": {
                "probability": round(landslide_prob, 4),
                "percentage": round(landslide_prob * 100, 1),
                "severity": landslide_severity,
                "confidence_interval": landslide_ci,
                "models_used": v1_result.get("landslide_models", []) + v2_result.get("landslide_models", []) if v2_result else v1_result.get("landslide_models", [])
            },
            "combined_risk": round(max(flood_prob, landslide_prob), 4),
            "explainability": shap_data,
            "processing_ms": processing_ms,
            "engine_version": "v2" if v2_result else "v1"
        }
    
    def _predict_v1(self, features: Dict) -> Dict:
        """Run V1 model predictions."""
        if not self.v1_models or not self.scaler:
            return {"flood_prob": 0.0, "landslide_prob": 0.0, "flood_models": [], "landslide_models": []}
        
        core_cols = self.feature_cols or [
            "lat", "lon", "elevation", "slope", "ndwi", "ndvi",
            "rain_24h", "rain_72h", "soil_moisture", "sar_backscatter"
        ]
        
        vector = [float(features.get(c, 0)) for c in core_cols]
        X = np.array([vector])
        X_scaled = self.scaler.transform(X)
        
        flood_prob = 0.0
        landslide_prob = 0.0
        
        if "xgb_flood" in self.v1_models:
            flood_prob = float(self.v1_models["xgb_flood"].predict_proba(X_scaled)[0][1])
        
        if "rf_landslide" in self.v1_models:
            landslide_prob = float(self.v1_models["rf_landslide"].predict_proba(X_scaled)[0][1])
        
        return {
            "flood_prob": flood_prob,
            "landslide_prob": landslide_prob,
            "flood_models": ["xgb_v1"],
            "landslide_models": ["rf_v1"]
        }
    
    def _predict_v2(self, features: Dict) -> Optional[Dict]:
        """Run V2 ensemble model predictions."""
        if not self.v2_flood or not self.v2_flood.models:
            return None
        
        try:
            from .feature_engineering import feature_engineer
            
            # Use loaded V2 feature columns if available, otherwise fallback to extended_cols
            # Use loaded V2 feature columns if available, otherwise fallback to extended_cols
            if hasattr(self, 'feature_cols_v2') and self.feature_cols_v2:
                cols = self.feature_cols_v2
            else:
                from .config import EXTENDED_FEATURES
                cols = EXTENDED_FEATURES + feature_engineer.get_engineered_feature_names()
                
            engineered = feature_engineer.engineer_single_sample(features)
            
            vector = [float(engineered.get(c, 0)) for c in cols]
            X = np.array([vector])
            
            # Apply scaler_v2 if loaded, fallback to feature_engineer transform
            if hasattr(self, 'scaler_v2') and self.scaler_v2:
                X = self.scaler_v2.transform(X)
            elif feature_engineer.fitted:
                X = feature_engineer.transform(X)
            
            flood_prob = float(self.v2_flood.ensemble_predict_proba(X)[0])
            landslide_prob = float(self.v2_landslide.ensemble_predict_proba(X)[0]) if self.v2_landslide and self.v2_landslide.models else 0.0
            
            return {
                "flood_prob": flood_prob,
                "landslide_prob": landslide_prob,
                "flood_models": list(self.v2_flood.models.keys()),
                "landslide_models": list(self.v2_landslide.models.keys()) if self.v2_landslide else []
            }
        except Exception as e:
            logger.debug(f"V2 prediction failed: {e}")
            return None
    
    def _compute_confidence_interval(self, v1, v2, hazard: str) -> Dict:
        """Compute confidence interval from model disagreement."""
        key = f"{hazard}_prob"
        values = [v1[key]]
        if v2:
            values.append(v2[key])
        
        mean_p = np.mean(values)
        std_p = np.std(values) if len(values) > 1 else 0.05
        
        return {
            "lower": round(max(0, mean_p - 1.96 * std_p), 4),
            "upper": round(min(1, mean_p + 1.96 * std_p), 4),
            "confidence": round(max(0.5, 1 - std_p * 5), 2)
        }
    
    def _classify_severity(self, prob: float) -> str:
        if prob >= 0.75:
            return "Extreme"
        elif prob >= 0.50:
            return "High"
        elif prob >= 0.25:
            return "Moderate"
        return "Low"
    
    def _generate_explanation(self, features: Dict, flood_p: float,
                               landslide_p: float, lang: str) -> Dict:
        """Generate simplified SHAP-like explanation."""
        rain = features.get("rain_24h", 0)
        slope = features.get("slope", 5)
        ndwi = features.get("ndwi", 0)
        elevation = features.get("elevation", 100)
        soil_moisture = features.get("soil_moisture", 50)
        
        total_risk = max(flood_p, landslide_p)
        
        # Weight factors
        w_rain = min(0.40, (rain / 120) * 0.40)
        w_slope = min(0.30, (slope / 45) * 0.30)
        w_ndwi = min(0.15, max(0, ndwi) / 0.6 * 0.15)
        w_sm = min(0.15, (soil_moisture / 100) * 0.15)
        
        total_w = max(w_rain + w_slope + w_ndwi + w_sm, 0.01)
        
        contributions = [
            {"feature": "Precipitation", "value": round(w_rain / total_w * total_risk, 3),
             "raw": round(rain, 1), "unit": "mm"},
            {"feature": "Slope", "value": round(w_slope / total_w * total_risk, 3),
             "raw": round(slope, 1), "unit": "°"},
            {"feature": "NDWI", "value": round(w_ndwi / total_w * total_risk, 3),
             "raw": round(ndwi, 4), "unit": ""},
            {"feature": "Soil Moisture", "value": round(w_sm / total_w * total_risk, 3),
             "raw": round(soil_moisture, 1), "unit": "%"},
            {"feature": "Elevation", "value": round(max(0, 1 - elevation / 500) * 0.1, 3),
             "raw": round(elevation, 1), "unit": "m"}
        ]
        
        return {
            "contributions": sorted(contributions, key=lambda x: -x["value"]),
            "risk_score": round(total_risk * 100, 1)
        }
    
    def status(self) -> Dict:
        return {
            "ready": self.ready,
            "v1_models": list(self.v1_models.keys()),
            "v2_flood_models": list(self.v2_flood.models.keys()) if self.v2_flood else [],
            "v2_landslide_models": list(self.v2_landslide.models.keys()) if self.v2_landslide else [],
            "feature_columns": self.feature_cols
        }


# Module-level singleton
try:
    inference_engine = MultiHazardInferenceEngine()
except Exception as e:
    logger.warning(f"Inference engine init deferred: {e}")
    inference_engine = None
