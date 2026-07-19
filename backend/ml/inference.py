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
import torch

logger = logging.getLogger("geoshield.ml.inference")
MODEL_DIR = Path(__file__).resolve().parent.parent / "model_dir"

# Import PyTorch classes
try:
    from .deep_learning_models import (
        FloodLSTM, FloodCNNLSTM, LandslideCNN, LandslideLSTM, PyTorchClassifierWrapper
    )
except ImportError:
    # Handle direct scripts running without packages
    from ml.deep_learning_models import (
        FloodLSTM, FloodCNNLSTM, LandslideCNN, LandslideLSTM, PyTorchClassifierWrapper
    )


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
            # V1 models
            if (MODEL_DIR / "scaler.pkl").exists():
                self.scaler = joblib.load(MODEL_DIR / "scaler.pkl")
                self.feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
                self.v1_models["xgb_flood"] = joblib.load(MODEL_DIR / "xgb_flood.pkl")
                self.v1_models["rf_landslide"] = joblib.load(MODEL_DIR / "rf_landslide.pkl")
                logger.info("V1 models loaded successfully.")
            
            # V2 models (advanced tree suite)
            try:
                # Handle import path difference in endpoints vs ML tests
                try:
                    from .flood_models import FloodModelSuite
                    from .landslide_models import LandslideModelSuite
                except ImportError:
                    from ml.flood_models import FloodModelSuite
                    from ml.landslide_models import LandslideModelSuite
                
                self.v2_flood = FloodModelSuite()
                self.v2_flood.load_models("flood_v2")
                
                self.v2_landslide = LandslideModelSuite()
                self.v2_landslide.load_models("landslide_v2")
                
                if (MODEL_DIR / "scaler_v2.pkl").exists():
                    self.scaler_v2 = joblib.load(MODEL_DIR / "scaler_v2.pkl")
                if (MODEL_DIR / "feature_cols_v2.pkl").exists():
                    self.feature_cols_v2 = joblib.load(MODEL_DIR / "feature_cols_v2.pkl")
                
                if self.v2_flood.models:
                    logger.info(f"V2 flood tree models loaded: {list(self.v2_flood.models.keys())}")
                if self.v2_landslide.models:
                    logger.info(f"V2 landslide tree models loaded: {list(self.v2_landslide.models.keys())}")
            except Exception as e:
                logger.debug(f"V2 tree models loading deferred/failed: {e}")

            # V2 PyTorch models
            try:
                lstm_path = MODEL_DIR / "flood_v2_lstm.pth"
                if lstm_path.exists():
                    net = FloodLSTM()
                    net.load_state_dict(torch.load(lstm_path, map_location="cpu"))
                    self.v2_lstm = PyTorchClassifierWrapper(net, "FloodLSTM")
                    logger.info("V2 FloodLSTM model loaded successfully.")

                cnnlstm_path = MODEL_DIR / "flood_v2_cnn_lstm.pth"
                if cnnlstm_path.exists():
                    net = FloodCNNLSTM()
                    net.load_state_dict(torch.load(cnnlstm_path, map_location="cpu"))
                    self.v2_cnn_lstm = PyTorchClassifierWrapper(net, "FloodCNNLSTM")
                    logger.info("V2 FloodCNNLSTM model loaded successfully.")

                slidecnn_path = MODEL_DIR / "landslide_v2_cnn.pth"
                if slidecnn_path.exists():
                    net = LandslideCNN()
                    net.load_state_dict(torch.load(slidecnn_path, map_location="cpu"))
                    self.v2_cnn = PyTorchClassifierWrapper(net, "LandslideCNN")
                    logger.info("V2 LandslideCNN model loaded successfully.")

                slidelstm_path = MODEL_DIR / "landslide_v2_lstm.pth"
                if slidelstm_path.exists():
                    net = LandslideLSTM()
                    net.load_state_dict(torch.load(slidelstm_path, map_location="cpu"))
                    self.v2_lstm_slide = PyTorchClassifierWrapper(net, "LandslideLSTM")
                    logger.info("V2 LandslideLSTM model loaded successfully.")
            except Exception as e:
                logger.debug(f"V2 deep learning models loading deferred/failed: {e}")
            
            self.ready = bool(self.v1_models or (self.v2_flood and self.v2_flood.models))
            
        except Exception as e:
            logger.warning(f"Model loading failed: {e}. Run training pipeline first.")
            self.ready = False
    
    def predict(self, features: Dict, lang: str = "en") -> Dict:
        """
        Run multi-hazard prediction from a feature dictionary.
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
            flood_prob = v2_result["flood_prob"] * 0.7 + v1_result["flood_prob"] * 0.3
            landslide_prob = v2_result["landslide_prob"] * 0.7 + v1_result["landslide_prob"] * 0.3
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
        
        models_used = v1_result.get("flood_models", [])
        if v2_result:
            models_used += v2_result.get("flood_models", [])

        slide_models_used = v1_result.get("landslide_models", [])
        if v2_result:
            slide_models_used += v2_result.get("landslide_models", [])

        return {
            "flood": {
                "probability": round(flood_prob, 4),
                "percentage": round(flood_prob * 100, 1),
                "severity": flood_severity,
                "confidence_interval": flood_ci,
                "models_used": models_used
            },
            "landslide": {
                "probability": round(landslide_prob, 4),
                "percentage": round(landslide_prob * 100, 1),
                "severity": landslide_severity,
                "confidence_interval": landslide_ci,
                "models_used": slide_models_used
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
        
        # Map latitude/longitude to match core cols keys lat/lon
        features_mapped = features.copy()
        if 'lat' not in features_mapped and 'latitude' in features_mapped:
            features_mapped['lat'] = features_mapped['latitude']
        if 'lon' not in features_mapped and 'longitude' in features_mapped:
            features_mapped['lon'] = features_mapped['longitude']

        vector = [float(features_mapped.get(c, 0.0)) for c in core_cols]
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
            try:
                from .feature_engineering import feature_engineer
            except ImportError:
                from ml.feature_engineering import feature_engineer
            
            # Use loaded V2 feature columns if available
            if hasattr(self, 'feature_cols_v2') and self.feature_cols_v2:
                cols = self.feature_cols_v2
            else:
                cols = feature_engineer.get_feature_names()
                
            engineered = feature_engineer.engineer_single_sample(features)
            vector = [float(engineered.get(c, 0.0)) for c in cols]
            X = np.array([vector])
            
            # Apply scaler_v2 if loaded, fallback to feature_engineer transform
            if hasattr(self, 'scaler_v2') and self.scaler_v2:
                X = self.scaler_v2.transform(X)
            elif feature_engineer.fitted:
                X = feature_engineer.transform(X)
            
            # Tree models predictions
            flood_tree_p = float(self.v2_flood.ensemble_predict_proba(X)[0])
            landslide_tree_p = float(self.v2_landslide.ensemble_predict_proba(X)[0]) if self.v2_landslide and self.v2_landslide.models else 0.0
            
            # PyTorch models predictions
            flood_lstm_p = float(self.v2_lstm.predict_proba(X)[0][1]) if hasattr(self, 'v2_lstm') else flood_tree_p
            flood_cnnlstm_p = float(self.v2_cnn_lstm.predict_proba(X)[0][1]) if hasattr(self, 'v2_cnn_lstm') else flood_tree_p
            
            landslide_cnn_p = float(self.v2_cnn.predict_proba(X)[0][1]) if hasattr(self, 'v2_cnn') else landslide_tree_p
            landslide_lstm_p = float(self.v2_lstm_slide.predict_proba(X)[0][1]) if hasattr(self, 'v2_lstm_slide') else landslide_tree_p
            
            # Advanced Blend (70% Trees, 15% LSTM, 15% CNN-LSTM)
            flood_prob = flood_tree_p * 0.70 + flood_lstm_p * 0.15 + flood_cnnlstm_p * 0.15
            landslide_prob = landslide_tree_p * 0.80 + landslide_cnn_p * 0.10 + landslide_lstm_p * 0.10
            
            models_list = list(self.v2_flood.models.keys())
            if hasattr(self, 'v2_lstm'):
                models_list.append("lstm_v2")
            if hasattr(self, 'v2_cnn_lstm'):
                models_list.append("cnnlstm_v2")

            slide_models_list = list(self.v2_landslide.models.keys()) if self.v2_landslide else []
            if hasattr(self, 'v2_cnn'):
                slide_models_list.append("cnn_v2")
            if hasattr(self, 'v2_lstm_slide'):
                slide_models_list.append("lstm_v2")
            
            return {
                "flood_prob": flood_prob,
                "landslide_prob": landslide_prob,
                "flood_models": models_list,
                "landslide_models": slide_models_list
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
        """Generate actual SHAP explanation using the SHAPExplainer."""
        try:
            try:
                from .shap_explainer import shap_explainer
            except ImportError:
                from ml.shap_explainer import shap_explainer
            
            cols = self.feature_cols_v2 if hasattr(self, 'feature_cols_v2') and self.feature_cols_v2 else self.feature_cols
            if not cols:
                try:
                    from .feature_engineering import feature_engineer
                except ImportError:
                    from ml.feature_engineering import feature_engineer
                cols = feature_engineer.get_feature_names()
                
            try:
                from .feature_engineering import feature_engineer
            except ImportError:
                from ml.feature_engineering import feature_engineer
                
            engineered = feature_engineer.engineer_single_sample(features)
            vector = [float(engineered.get(c, 0.0)) for c in cols]
            X = np.array(vector)
            
            if hasattr(self, 'scaler_v2') and self.scaler_v2:
                X_scaled = self.scaler_v2.transform([X])[0]
            elif self.scaler:
                X_scaled = self.scaler.transform([X])[0]
            else:
                X_scaled = X
                
            if flood_p >= landslide_p:
                model = self.v2_flood.models.get("xgb") if (self.v2_flood and "xgb" in self.v2_flood.models) else self.v1_models.get("xgb_flood")
                hazard = "flood"
                prob = flood_p
            else:
                model = self.v2_landslide.models.get("rf") if (self.v2_landslide and "rf" in self.v2_landslide.models) else self.v1_models.get("rf_landslide")
                hazard = "landslide"
                prob = landslide_p
                
            if model is None:
                return {"error": "No model loaded for explanation"}
                
            # Calibrated tree models are stored as CalibratedClassifierCV wrappers, so we extract the base estimator
            base_model = getattr(model, "estimator", model)
                
            explanation = shap_explainer.explain_prediction(
                model=base_model,
                X_sample=X_scaled,
                feature_names=cols,
                prediction_prob=prob,
                hazard_type=hazard,
                lang=lang
            )
            return explanation
        except Exception as e:
            logger.warning(f"Failed to generate SHAP explanation: {e}")
            return {
                "contributions": [
                    {"feature": "Precipitation", "value": 0.5, "raw_input": float(features.get("rain_24h", 0)), "unit": "mm"},
                    {"feature": "Slope", "value": 0.3, "raw_input": float(features.get("slope", 5)), "unit": "°"}
                ],
                "explanation": f"Explanation generated using fallback mock due to error: {e}",
                "risk_score": float(max(flood_p, landslide_p) * 100)
            }
    
    def status(self) -> Dict:
        return {
            "ready": self.ready,
            "v1_models": list(self.v1_models.keys()),
            "v2_flood_models": list(self.v2_flood.models.keys()) if self.v2_flood else [],
            "v2_landslide_models": list(self.v2_landslide.models.keys()) if self.v2_landslide else [],
            "v2_lstm_loaded": hasattr(self, 'v2_lstm'),
            "v2_cnn_lstm_loaded": hasattr(self, 'v2_cnn_lstm'),
            "v2_cnn_loaded": hasattr(self, 'v2_cnn'),
            "v2_lstm_slide_loaded": hasattr(self, 'v2_lstm_slide'),
            "feature_columns": self.feature_cols
        }


# Module-level singleton
try:
    inference_engine = MultiHazardInferenceEngine()
except Exception as e:
    logger.warning(f"Inference engine init deferred: {e}")
    inference_engine = None
