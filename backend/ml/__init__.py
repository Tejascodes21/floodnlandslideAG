"""
GeoShield AI — Advanced ML/DL Pipeline Package
================================================
Research-grade machine learning models for flood and landslide prediction.

Includes:
  - Advanced synthetic dataset generation
  - Feature engineering pipeline  
  - Flood models (RF, XGBoost, LSTM, CNN-LSTM, Ensemble)
  - Landslide models (CNN, RF, XGBoost, LSTM, Ensemble)
  - SHAP explainability
  - Model versioning and registry
  - Production inference engine
"""

from .inference import MultiHazardInferenceEngine, inference_engine

__all__ = ["MultiHazardInferenceEngine", "inference_engine"]
