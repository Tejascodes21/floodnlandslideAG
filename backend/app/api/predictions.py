"""
Predictions API Endpoint
=========================
Exposes the advanced multi-hazard inference engine and GEE pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional, List
from pathlib import Path
import json

import logging

logger = logging.getLogger("geoshield.api")

try:
    # These live at backend/services/ and backend/ml/ (CWD is backend/)
    from services.gee.pipeline import gee_pipeline
    from ml.inference import inference_engine
except ImportError as e:
    logger.error(f"Failed to import ML/GEE pipelines: {e}")
    gee_pipeline = None
    inference_engine = None

router = APIRouter()

# Path to the persisted advanced evaluation results (ml/results/advanced_evaluation_v2.json)
_RESULTS_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "results" / "advanced_evaluation_v2.json"

class PredictionRequest(BaseModel):
    lat: float
    lon: float
    lang: Optional[str] = "en"
    include_timeseries: Optional[bool] = False
    
class BatchPredictionRequest(BaseModel):
    points: List[Dict[str, float]] # list of {"lat": ..., "lon": ...}
    lang: Optional[str] = "en"

@router.post("/advanced")
async def advanced_prediction(request: PredictionRequest):
    """
    Runs the full advanced GEE + ML inference pipeline.
    """
    if not gee_pipeline or not inference_engine:
        raise HTTPException(status_code=503, detail="Advanced pipeline not initialized")
        
    try:
        # 1. Extract features using GEE pipeline
        features = gee_pipeline.extract_full_features(
            request.lat, request.lon, include_timeseries=request.include_timeseries
        )
        
        # 2. Run multi-hazard inference
        prediction = inference_engine.predict(features, lang=request.lang)
        
        return {
            "status": "success",
            "coordinates": {"lat": request.lat, "lon": request.lon},
            "features_extracted": len(features),
            "prediction": prediction,
            "geospatial_metadata": {
                "climate_zone": features.get("_climate_zone"),
                "soil_type": features.get("_soil_type"),
                "terrain_class": features.get("_terrain_class"),
                "source": features.get("_source")
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/heatmap")
async def generate_risk_heatmap(request: PredictionRequest):
    """
    Generates a spatial risk distribution grid around the target point.
    """
    if not gee_pipeline:
        raise HTTPException(status_code=503, detail="GEE pipeline not initialized")
        
    try:
        heatmap_data = gee_pipeline.generate_risk_heatmap(
            request.lat, request.lon, grid_size=8, cell_size_m=500
        )
        return {"status": "success", "data": heatmap_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/comparison")
async def get_model_comparison():
    """
    Returns the per-model evaluation metrics from the last training run so the
    frontend can render the side-by-side model comparison deck. Reads the
    persisted advanced_evaluation_v2.json produced by ml/train_advanced.py.
    """
    if not _RESULTS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No evaluation results found. Run the advanced training "
                   "pipeline first: `python -m ml.train_advanced`.",
        )
    try:
        with open(_RESULTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # Surface only the chart-relevant parts to keep the payload lean
        return {
            "status": "success",
            "dataset": {
                "n_samples": data.get("dataset", {}).get("n_samples"),
                "n_features": data.get("dataset", {}).get("n_features"),
            },
            "flood_models": data.get("flood_models", {}),
            "landslide_models": data.get("landslide_models", {}),
            "flood_feature_importance": data.get("flood_feature_importance", [])[:10],
            "landslide_feature_importance": data.get("landslide_feature_importance", [])[:10],
            "roc_data": data.get("roc_data", {}),
            "cross_validation": data.get("cross_validation", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
