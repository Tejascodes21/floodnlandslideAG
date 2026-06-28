"""
SHAP Explainability Engine
=============================
Real SHAP-based feature contribution analysis for model predictions.
Generates waterfall data, feature importance rankings, and
natural language explanations in multiple languages.
"""

import numpy as np
import logging
from typing import Dict, List

logger = logging.getLogger("geoshield.ml.shap")

# Feature descriptions for natural language explanations
FEATURE_DESCRIPTIONS = {
    "en": {
        "rain_24h": "24-hour rainfall accumulation ({val}mm)",
        "rain_72h": "3-day rainfall accumulation ({val}mm)",
        "rain_7d": "7-day rainfall accumulation ({val}mm)",
        "slope": "Terrain slope angle ({val}°)",
        "elevation": "Ground elevation ({val}m ASL)",
        "ndwi": "Water body index NDWI ({val})",
        "ndvi": "Vegetation density NDVI ({val})",
        "mndwi": "Modified water index MNDWI ({val})",
        "evi": "Enhanced vegetation index EVI ({val})",
        "soil_moisture": "Soil moisture saturation ({val}%)",
        "sar_backscatter": "SAR radar backscatter ({val} dB)",
        "sar_vh": "SAR cross-polarization backscatter ({val} dB)",
        "drainage_density": "Drainage network density ({val} km/km²)",
        "river_proximity": "Distance to nearest river ({val} km)",
        "river_distance": "Distance to nearest river ({val} km)",
        "terrain_roughness": "Terrain surface roughness ({val})",
        "twi": "Topographic wetness index ({val})",
        "spi": "Standardized precipitation index ({val})",
        "aspect": "Slope aspect direction ({val}°)",
        "curvature": "Terrain curvature ({val})",
        "historical_flood_freq": "Historical flood frequency ({val}/decade)",
        "historical_events": "Historical disaster count ({val} events)",
        "flow_accumulation": "Hydrological flow accumulation ({val})",
        "slope_rainfall_interaction": "Slope & rainfall interaction ({val})",
        "soil_saturation_index": "Soil moisture & rainfall saturation ({val})",
        "vegetation_degradation_index": "Vegetation loss & rainfall interaction ({val})",
        "terrain_instability_score": "Terrain instability score ({val})",
        "rainfall_accumulation": "Cumulative rainfall score ({val}mm)",
        "river_proximity_factor": "River proximity factor ({val})",
        "upstream_catchment_indicator": "Upstream catchment flow factor ({val})"
    },
    "hi": {
        "rain_24h": "24 घंटे की वर्षा ({val}mm)",
        "rain_72h": "3 दिन की संचयी वर्षा ({val}mm)",
        "slope": "भूमि का ढलान कोण ({val}°)",
        "elevation": "समुद्र तल से ऊंचाई ({val}m)",
        "ndwi": "जल निकाय सूचकांक NDWI ({val})",
        "ndvi": "वनस्पति घनत्व NDVI ({val})",
        "soil_moisture": "मिट्टी की नमी ({val}%)",
        "sar_backscatter": "SAR रडार प्रतिध्वनि ({val} dB)",
        "drainage_density": "जल निकासी घनत्व ({val} km/km²)",
        "river_proximity": "नदी से दूरी ({val} km)",
        "terrain_roughness": "भूभाग खुरदरापन ({val})",
        "twi": "स्थलाकृतिक आर्द्रता सूचकांक ({val})",
        "soil_saturation_index": "मृदा संतृप्ति स्तर ({val})",
        "terrain_instability_score": "भूभाग अस्थिरता सूचकांक ({val})"
    },
    "mr": {
        "rain_24h": "24 तासांचा पाऊस ({val}mm)",
        "rain_72h": "3 दिवसांचा एकूण पाऊस ({val}mm)",
        "slope": "जमिनीचा उतार ({val}°)",
        "elevation": "समुद्रसपाटीपासून उंची ({val}m)",
        "ndwi": "पाण्याचा निर्देशांक NDWI ({val})",
        "ndvi": "वनस्पती घनता NDVI ({val})",
        "soil_moisture": "मातीतील ओलावा ({val}%)",
        "sar_backscatter": "SAR रडार प्रतिध्वनी ({val} dB)",
        "drainage_density": "पाणी निचरा घनता ({val} km/km²)",
        "river_proximity": "नदीपासून अंतर ({val} km)",
        "soil_saturation_index": "मातीची संपृक्तता पातळी ({val})",
        "terrain_instability_score": "डोंगराळ भूभाग अस्थिरता पातळी ({val})"
    }
}


class SHAPExplainer:
    """
    Generates SHAP-style feature contribution explanations.
    
    For tree-based models (XGBoost, RF), uses TreeSHAP algorithm
    when shap library is available, otherwise uses permutation-based
    approximation.
    """
    
    def __init__(self):
        self._shap_available = False
        try:
            import shap
            self._shap_available = True
        except ImportError:
            logger.info("SHAP library not installed. Using approximation mode.")
    
    def explain_prediction(self, model, X_sample: np.ndarray,
                           feature_names: List[str],
                           prediction_prob: float,
                           hazard_type: str = "flood",
                           lang: str = "en") -> Dict:
        """
        Generate SHAP explanation for a single prediction.
        
        Returns:
            Dict with SHAP values, ranked features, waterfall data,
            and natural language explanation
        """
        shap_values = self._compute_shap_values(model, X_sample, feature_names)
        
        # Rank features by absolute contribution
        ranked = sorted(shap_values, key=lambda x: abs(x["value"]), reverse=True)
        
        # Generate waterfall data (cumulative)
        waterfall = self._generate_waterfall(ranked, prediction_prob)
        
        # Natural language explanation
        explanation = self._generate_nl_explanation(ranked, prediction_prob, hazard_type, lang)
        
        return {
            "hazard_type": hazard_type,
            "prediction_probability": round(prediction_prob, 4),
            "shap_values": ranked,
            "waterfall": waterfall,
            "top_drivers": ranked[:5],
            "explanation": explanation,
            "language": lang
        }
    
    def _compute_shap_values(self, model, X_sample: np.ndarray,
                              feature_names: List[str]) -> List[Dict]:
        """Compute SHAP values using TreeSHAP or approximation."""
        
        if self._shap_available and hasattr(model, 'feature_importances_'):
            try:
                import shap
                explainer = shap.TreeExplainer(model)
                sv = explainer.shap_values(X_sample.reshape(1, -1))
                
                if isinstance(sv, list):
                    sv = sv[1]  # Take positive class
                sv = sv.flatten()
                
                return [
                    {"feature": feature_names[i], "value": round(float(sv[i]), 4),
                     "raw_input": round(float(X_sample[i]), 4),
                     "direction": "increases" if sv[i] > 0 else "decreases"}
                    for i in range(min(len(feature_names), len(sv)))
                ]
            except Exception as e:
                logger.debug(f"TreeSHAP failed, using approximation: {e}")
        
        # Permutation-based approximation
        return self._approximate_shap(model, X_sample, feature_names)
    
    def _approximate_shap(self, model, X_sample: np.ndarray,
                           feature_names: List[str]) -> List[Dict]:
        """
        Approximate SHAP values using feature importance weighted
        by the sample's deviation from the training mean.
        """
        n_features = len(X_sample)
        
        # Get feature importances if available
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_[:n_features]
        else:
            importances = np.ones(n_features) / n_features
        
        # Baseline prediction
        try:
            base_prob = model.predict_proba(X_sample.reshape(1, -1))[0, 1]
        except Exception:
            base_prob = 0.5
        
        # Approximate each feature's contribution
        contributions = []
        for i in range(min(n_features, len(feature_names))):
            # Perturb feature to zero and measure change
            X_perturbed = X_sample.copy()
            X_perturbed[i] = 0
            
            try:
                perturbed_prob = model.predict_proba(X_perturbed.reshape(1, -1))[0, 1]
                contribution = base_prob - perturbed_prob
            except Exception:
                contribution = importances[i] * X_sample[i] * 0.01
            
            contributions.append({
                "feature": feature_names[i],
                "value": round(float(contribution), 4),
                "raw_input": round(float(X_sample[i]), 4),
                "importance": round(float(importances[i]), 4),
                "direction": "increases" if contribution > 0 else "decreases"
            })
        
        return contributions
    
    def _generate_waterfall(self, ranked: List[Dict], prediction: float) -> List[Dict]:
        """Generate waterfall chart data showing cumulative risk buildup."""
        baseline = 0.5  # Assume 50% prior
        cumulative = baseline
        waterfall = [{"step": "baseline", "value": round(baseline, 4), "cumulative": round(baseline, 4)}]
        
        for feat in ranked[:8]:  # Top 8 features
            cumulative += feat["value"]
            waterfall.append({
                "step": feat["feature"],
                "value": round(feat["value"], 4),
                "cumulative": round(min(max(cumulative, 0), 1), 4)
            })
        
        waterfall.append({"step": "prediction", "value": round(prediction, 4), "cumulative": round(prediction, 4)})
        return waterfall
    
    def _generate_nl_explanation(self, ranked: List[Dict], prediction: float,
                                  hazard_type: str, lang: str) -> str:
        """Generate natural language explanation in the specified language."""
        lang = lang if lang in FEATURE_DESCRIPTIONS else "en"
        descs = FEATURE_DESCRIPTIONS[lang]
        
        severity = "extreme" if prediction > 0.75 else ("high" if prediction > 0.5 else ("moderate" if prediction > 0.25 else "low"))
        
        headers = {
            "en": f"{hazard_type.title()} risk is {severity} ({prediction*100:.1f}%) due to:",
            "hi": f"{hazard_type.title()} का खतरा {severity} ({prediction*100:.1f}%) है, कारण:",
            "mr": f"{hazard_type.title()} चा धोका {severity} ({prediction*100:.1f}%) आहे, कारणे:"
        }
        
        lines = [headers.get(lang, headers["en"])]
        
        for feat in ranked[:4]:
            fname = feat["feature"]
            if fname in descs:
                desc = descs[fname].format(val=feat["raw_input"])
                direction_text = {"en": "↑ risk", "hi": "↑ खतरा", "mr": "↑ धोका"}.get(lang, "↑ risk")
                if feat["direction"] == "decreases":
                    direction_text = {"en": "↓ risk", "hi": "↓ खतरा", "mr": "↓ धोका"}.get(lang, "↓ risk")
                lines.append(f"  • {desc} → {direction_text}")
        
        return "\n".join(lines)


shap_explainer = SHAPExplainer()
