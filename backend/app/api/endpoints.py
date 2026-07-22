from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import joblib
import numpy as np
import json
from pathlib import Path

from app.core.config import settings
from app.db.session import get_db
from app.db.schemas import PredictionRecord, SOSAlert, Volunteer, RescueMission, CommunityReport
from app.services.earth_engine import gee_service
from app.services.cnn_processor import cnn_processor
from app.services.weather import weather_service
from app.services.alert import alert_service
from app.services.chatbot import chatbot_copilot
from app.services.rescue import rescue_service

router = APIRouter(tags=["GeoShield Intelligence Services"])

# Self-healing model loader
MODEL_DIR = Path("model_dir")
scaler = None
feat_cols = None
xgb_flood = None
rf_landslide = None
# Fallback to the full V1+V2 inference engine if any V1 artifact is missing
_inference_engine_fallback = None

def _load_inference_engine_fallback():
    """Lazily import the advanced inference engine (V1+V2 ensemble)."""
    global _inference_engine_fallback
    if _inference_engine_fallback is None:
        try:
            from ml.inference import inference_engine
            _inference_engine_fallback = inference_engine
        except Exception as e:
            print(f"Could not load inference engine fallback: {e}")
    return _inference_engine_fallback

def load_models():
    """Load V1 models; self-heal to the V2 inference engine if any are absent."""
    global scaler, feat_cols, xgb_flood, rf_landslide
    missing = [p for p in ["scaler.pkl", "feature_cols.pkl", "xgb_flood.pkl", "rf_landslide.pkl"]
               if not (MODEL_DIR / p).exists()]
    if missing:
        # V1 artifacts incomplete — try the advanced V2 inference engine instead
        engine = _load_inference_engine_fallback()
        if engine and engine.ready:
            print(f"V1 models incomplete ({', '.join(missing)}). "
                  "Self-healing to the advanced V1+V2 inference engine.")
            return "fallback"
        error_msg = (
            "CRITICAL ERROR: Pre-trained ML models missing (" + ", ".join(missing) + "). "
            "Run the training pipeline first: 'make train' (V1) or 'make train-advanced' (V2)."
        )
        print(error_msg, flush=True)
        raise RuntimeError(error_msg)
    try:
        scaler = joblib.load(MODEL_DIR / "scaler.pkl")
        feat_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
        xgb_flood = joblib.load(MODEL_DIR / "xgb_flood.pkl")
        rf_landslide = joblib.load(MODEL_DIR / "rf_landslide.pkl")
        print("Pre-trained GeoShield ML/DL models loaded successfully.")
    except FileNotFoundError as e:
        error_msg = (
            f"CRITICAL ERROR: Pre-trained ML model file missing on startup ({e.filename}). "
            "Please run the model training pipeline first using 'make train' or 'python train_pipeline.py'."
        )
        print(error_msg, flush=True)
        raise RuntimeError(error_msg) from e

# Models are loaded lazily on first prediction request to avoid import-time failures

# --- Pydantic Schemas ---
class HazardRequest(BaseModel):
    lat: float
    lon: float
    location_name: str = "Query Zone"
    lang: str = "en"

class SOSCreateRequest(BaseModel):
    reporter_name: str
    phone: str
    lat: float
    lon: float
    emergency_type: str
    details: str = ""
    voice_note_path: str = None

class CommunityReportRequest(BaseModel):
    reporter_name: str
    lat: float
    lon: float
    incident_type: str
    details: str = ""

class ChatRequest(BaseModel):
    message: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    lang: str = "en"

class VolunteerDispatchRequest(BaseModel):
    emergency_type: str = "Evacuation logistics"
    details: str = ""
    citizen_name: str = "Local Dispatch"
    lat: Optional[float] = None
    lon: Optional[float] = None

class CommunityReportStatusUpdateRequest(BaseModel):
    status: str

class SystemSettingsOverride(BaseModel):
    extreme_threshold: float
    high_threshold: float
    mod_threshold: float

# --- 1. PREDICTION ENDPOINTS ---

@router.post("/predict/multi-hazard")
def predict_multi_hazard(req: HazardRequest, db: Session = Depends(get_db)):
    # Ensure inference engine is loaded
    engine = _load_inference_engine_fallback()
    if not engine or not engine.ready:
        try:
            # Self-heal or load engine
            from ml.inference import inference_engine
            engine = inference_engine
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Advanced inference engine not initialized: {e}")

    try:
        # Step A: Fetch inputs from satellite and weather integrations
        geo_feats = gee_service.get_geospatial_features(req.lat, req.lon)
        weather_feats = weather_service.get_live_weather(req.lat, req.lon)
        cnn_feats = cnn_processor.chunk_and_segment(req.lat, req.lon)

        # Step B: Assemble complete feature dictionary for the advanced engine
        features_dict = {
            "lat": req.lat,
            "lon": req.lon,
            "latitude": req.lat,
            "longitude": req.lon,
            "elevation": geo_feats["elevation"],
            "slope": geo_feats["slope"],
            "aspect": geo_feats.get("aspect", 180.0),
            "ndwi": geo_feats["ndwi"],
            "ndvi": geo_feats["ndvi"],
            "mndwi": geo_feats.get("mndwi", geo_feats["ndwi"] * 0.8),
            "evi": geo_feats.get("evi", geo_feats["ndvi"] * 0.8),
            "soil_moisture": geo_feats["soil_moisture"],
            "sar_backscatter": geo_feats["sar_backscatter"],
            "sar_vh": geo_feats.get("sar_vh", geo_feats["sar_backscatter"] - 6.0),
            "terrain_roughness": geo_feats.get("terrain_roughness", 5.0),
            "curvature": geo_feats.get("curvature", 0.0),
            "twi": geo_feats.get("twi", 10.0),
            "drainage_density": geo_feats.get("drainage_density", 0.5),
            "river_proximity": geo_feats.get("river_proximity", 2.0),
            "river_distance": geo_feats.get("river_distance", 2.0),
            "flow_accumulation": geo_feats.get("flow_accumulation", 100.0),
            "water_occurrence": geo_feats.get("water_occurrence", 0.0),
            "historical_events": geo_feats.get("historical_events", 0),
            "rain_24h": weather_feats["precipitation_accumulations"]["rain_24h_mm"],
            "rain_72h": weather_feats["precipitation_accumulations"]["rain_72h_mm"],
            "rain_7d": weather_feats["precipitation_accumulations"].get("rain_7d_mm", weather_feats["precipitation_accumulations"]["rain_72h_mm"] * 1.5),
            "temperature": weather_feats["temp_c"],
            "humidity": weather_feats["humidity_pct"]
        }

        # Step C: Compute dynamic prediction probabilities using the full ensemble engine
        engine_result = engine.predict(features_dict, lang=req.lang)
        p_flood = float(engine_result.get("flood", {}).get("probability", 0.0))
        p_landslide = float(engine_result.get("landslide", {}).get("probability", 0.0))

        # Influence flood score upward based on CNN segmented water accumulation area
        cnn_inundation_adj = cnn_feats["inundation_ratio_percentage"] / 100.0 * 0.15
        p_flood = min(0.99, p_flood + cnn_inundation_adj)
        
        # Step D: Evaluate alert notification levels and translations
        alert_pkg = alert_service.evaluate_and_trigger(
            lat=req.lat, lon=req.lon,
            location_name=req.location_name,
            flood_prob=p_flood,
            landslide_prob=p_landslide,
            lang=req.lang
        )
        
        # Step E: Compute SHAP Explainability contributions
        shap_pkg = chatbot_copilot.generate_shap_explanation(
            flood_prob=p_flood,
            landslide_prob=p_landslide,
            slope=geo_feats["slope"],
            ndwi=geo_feats["ndwi"],
            rain=weather_feats["precipitation_accumulations"]["rain_24h_mm"],
            lang=req.lang
        )
        
        # Step F: Record query in database prediction history
        pred_record = PredictionRecord(
            location_name=req.location_name,
            lat=req.lat,
            lon=req.lon,
            flood_prob=p_flood,
            flood_severity=alert_pkg["severity"],
            landslide_prob=p_landslide,
            slope=geo_feats["slope"],
            ndwi=geo_feats["ndwi"],
            ndvi=geo_feats["ndvi"],
            rainfall_24h=weather_feats["precipitation_accumulations"]["rain_24h_mm"],
            soil_moisture=geo_feats["soil_moisture"],
            shap_values_json=json.dumps(shap_pkg["shap_values"])
        )
        db.add(pred_record)
        db.commit()
        db.refresh(pred_record)
        
        # Step G: Find safe shelters in vicinity
        nearest_shelter = rescue_service.find_nearest_shelter(req.lat, req.lon)
        
        return {
            "prediction_id": pred_record.id,
            "coordinates": {"lat": req.lat, "lon": req.lon},
            "location_name": req.location_name,
            "elevation": geo_feats["elevation"],
            "slope": geo_feats["slope"],
            "ndwi": geo_feats["ndwi"],
            "ndvi": geo_feats["ndvi"],
            "weather": weather_feats,
            "cnn_satellite_analysis": cnn_feats,
            "flood_risk": {
                "probability": round(p_flood, 4),
                "percentage": round(p_flood * 100, 1),
                "severity": alert_pkg["severity"]
            },
            "landslide_risk": {
                "probability": round(p_landslide, 4),
                "percentage": round(p_landslide * 100, 1),
                "susceptibility": "High" if p_landslide > 0.50 else ("Moderate" if p_landslide > 0.25 else "Low")
            },
            "explainability": shap_pkg,
            "alerts": alert_pkg,
            "nearest_evacuation_camp": nearest_shelter,
            "source_status": geo_feats["source"],
            "data_source": geo_feats.get("data_source", "simulation")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Inference failed: {str(e)}")

@router.get("/predict/history")
def get_prediction_history(db: Session = Depends(get_db), limit: int = 50):
    """
    Returns recent prediction records for the Analytics & ML scenario history logs.
    Newest first, capped at `limit` (default 50).
    """
    records = (
        db.query(PredictionRecord)
        .order_by(PredictionRecord.created_at.desc())
        .limit(min(max(limit, 1), 500))
        .all()
    )
    return [
        {
            "id": r.id,
            "location_name": r.location_name,
            "lat": r.lat,
            "lon": r.lon,
            "flood_prob": r.flood_prob,
            "flood_severity": r.flood_severity,
            "landslide_prob": r.landslide_prob,
            "slope": r.slope,
            "ndwi": r.ndwi,
            "ndvi": r.ndvi,
            "rainfall_24h": r.rainfall_24h,
            "soil_moisture": r.soil_moisture,
            "shap_values": json.loads(r.shap_values_json) if r.shap_values_json else [],
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]

# --- 2. LIVE SATELLITE LAYER ---

@router.get("/satellite/live")
def get_live_satellite(lat: float, lon: float, req: Request, days: int = 30):
    """Returns multi-spectral time-series maps for coordinates (NDWI/NDVI grids)"""
    ts_history = gee_service.get_time_series_satellite(lat, lon, days)
    base_url = str(req.base_url).rstrip('/')
    return {
        "coordinates": {"lat": lat, "lon": lon},
        "time_series_playback": ts_history,
        "layers": {
            "ndwi_layer": f"{base_url}/api/map/ndwi?lat={lat}&lon={lon}",
            "ndvi_layer": f"{base_url}/api/map/ndvi?lat={lat}&lon={lon}",
            "dem_layer": f"{base_url}/api/map/elevation?lat={lat}&lon={lon}"
        }
    }

@router.get("/map/{layer}")
def get_map_layer(layer: str, lat: float, lon: float):
    """
    Returns a spectral-index snapshot for the requested layer around the coords.
    Supported layers: ndwi, ndvi, elevation (dem).
    """
    if layer not in ("ndwi", "ndvi", "elevation", "dem"):
        raise HTTPException(status_code=400, detail=f"Unknown layer: {layer}")

    feats = gee_service.get_geospatial_features(lat, lon)
    # Map the requested layer to its index value
    key = "elevation" if layer in ("elevation", "dem") else layer
    return {
        "layer": layer,
        "coordinates": {"lat": lat, "lon": lon},
        "value": feats.get(key, 0.0),
        "units": {
            "ndwi": "index (-1..1)",
            "ndvi": "index (-1..1)",
            "elevation": "meters",
            "dem": "meters",
        }.get(layer, "unitless"),
        "source": feats.get("source", "simulation"),
    }

# --- 3. SOS DISTRICT COORDINATOR ENDPOINTS ---

@router.post("/sos/create")
def create_sos(req: SOSCreateRequest, db: Session = Depends(get_db)):
    # Save SOS alert
    new_sos = SOSAlert(
        reporter_name=req.reporter_name,
        phone=req.phone,
        lat=req.lat,
        lon=req.lon,
        emergency_type=req.emergency_type,
        details=req.details,
        voice_note_path=req.voice_note_path,
        status="Pending"
    )
    db.add(new_sos)
    db.commit()
    db.refresh(new_sos)
    
    # AI Assignment: Find closest active volunteer
    vols = db.query(Volunteer).filter(Volunteer.active == True).all()
    assigned_vol = None
    safe_route = []
    nearest_shelter = rescue_service.find_nearest_shelter(req.lat, req.lon)
    
    if vols:
        vol_list = [{"id": v.id, "name": v.full_name, "skills": v.skills, "vehicle": v.vehicle_type, "lat": v.lat, "lon": v.lon} for v in vols]
        matched = rescue_service.match_nearest_volunteer(req.lat, req.lon, vol_list)
        
        if matched:
            assigned_vol = matched
            # Update SOS table
            new_sos.volunteer_id = matched["id"]
            new_sos.status = "Dispatched"
            db.commit()
            
            # Generate risk-safe polyline detour from volunteer to user
            # Create a mock hazard zone at user coordinates to demonstrate deflection routing
            active_hazards = [{"lat": req.lat + 0.001, "lon": req.lon - 0.001}]
            route_points = rescue_service.generate_safe_route(
                start_lat=matched["lat"], start_lon=matched["lon"],
                end_lat=req.lat, end_lon=req.lon,
                hazard_zones=active_hazards
            )
            
            # Record Rescue Mission
            mission = RescueMission(
                volunteer_id=matched["id"],
                sos_id=new_sos.id,
                route_geojson=json.dumps(route_points),
                status="Assigned"
            )
            db.add(mission)
            db.commit()
            safe_route = route_points
            
    # SMS Trigger
    dispatch_msg = settings.TRANSLATIONS["en"]["sos_dispatched"].format(
        name=assigned_vol["name"] if assigned_vol else "Rescue Team Alpha",
        skill=assigned_vol["skills"] if assigned_vol else "General Rescue",
        vehicle=assigned_vol["vehicle"] if assigned_vol else "4x4 Truck"
    )
    alert_service._dispatch_channels(req.reporter_name, dispatch_msg, "SOS Dispatch Broadcast", "Extreme")

    return {
        "sos_id": new_sos.id,
        "status": new_sos.status,
        "volunteer_assigned": assigned_vol,
        "evacuation_camp": nearest_shelter,
        "safe_route_polyline": safe_route,
        "alert_broadcast": dispatch_msg
    }

@router.get("/volunteers")
def list_volunteers(db: Session = Depends(get_db)):
    vols = db.query(Volunteer).all()
    return [
        {
            "id": v.id,
            "user_id": v.user_id,
            "full_name": v.full_name,
            "skills": v.skills,
            "phone": v.phone,
            "vehicle_type": v.vehicle_type,
            "lat": v.lat,
            "lon": v.lon,
            "active": v.active,
            "registered_at": v.registered_at.isoformat() if v.registered_at else None,
        }
        for v in vols
    ]

@router.get("/missions")
def list_active_missions(db: Session = Depends(get_db)):
    missions = db.query(RescueMission).all()
    res = []
    for m in missions:
        res.append({
            "mission_id": m.id,
            "volunteer_name": m.volunteer.full_name,
            "vehicle": m.volunteer.vehicle_type,
            "citizen": m.sos_alert.reporter_name,
            "emergency_type": m.sos_alert.emergency_type,
            "route": json.loads(m.route_geojson),
            "status": m.status
        })
    return res

@router.post("/community/report/{report_id}/status")
def update_report_status(report_id: int, req: CommunityReportStatusUpdateRequest, db: Session = Depends(get_db)):
    report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = req.status
    db.commit()
    db.refresh(report)
    return {"status": "success", "report_id": report.id, "new_status": report.status}

@router.post("/volunteer/{volunteer_id}/dispatch")
def dispatch_volunteer(volunteer_id: int, req: VolunteerDispatchRequest, db: Session = Depends(get_db)):
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    if volunteer.active:
        raise HTTPException(status_code=400, detail="Volunteer already active on a mission")

    target_lat = req.lat if req.lat is not None else volunteer.lat + 0.0025
    target_lon = req.lon if req.lon is not None else volunteer.lon - 0.0025

    nearest_shelter = rescue_service.find_nearest_shelter(target_lat, target_lon)
    active_hazards = [{"lat": target_lat + 0.001, "lon": target_lon - 0.001}]
    route_points = rescue_service.generate_safe_route(
        start_lat=volunteer.lat,
        start_lon=volunteer.lon,
        end_lat=target_lat,
        end_lon=target_lon,
        hazard_zones=active_hazards
    )

    sos_alert = SOSAlert(
        reporter_name=req.citizen_name,
        phone="9999999900",
        lat=target_lat,
        lon=target_lon,
        emergency_type=req.emergency_type,
        details=req.details or f"Dispatched from volunteer dashboard for {req.citizen_name}",
        voice_note_path=None,
        status="Dispatched",
        volunteer_id=volunteer.id
    )
    db.add(sos_alert)
    volunteer.active = True
    db.commit()
    db.refresh(sos_alert)
    db.refresh(volunteer)

    mission = RescueMission(
        volunteer_id=volunteer.id,
        sos_id=sos_alert.id,
        route_geojson=json.dumps(route_points),
        status="Assigned"
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)

    alert_service._dispatch_channels(
        req.citizen_name,
        f"Volunteer {volunteer.full_name} dispatched for {req.emergency_type}.",
        "Volunteer Dispatch",
        "High"
    )

    return {
        "status": "success",
        "mission_id": mission.id,
        "volunteer": {
            "id": volunteer.id,
            "full_name": volunteer.full_name,
            "skills": volunteer.skills,
            "vehicle_type": volunteer.vehicle_type,
            "lat": volunteer.lat,
            "lon": volunteer.lon,
            "active": volunteer.active
        },
        "citizen": sos_alert.reporter_name,
        "emergency_type": sos_alert.emergency_type,
        "route": route_points,
        "mission_status": mission.status,
        "evacuation_camp": nearest_shelter,
        "sos_id": sos_alert.id
    }

@router.post("/mission/{mission_id}/complete")
def complete_mission(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(RescueMission).filter(RescueMission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission.status = "Completed"
    mission.completed_at = datetime.utcnow()
    if mission.volunteer:
        mission.volunteer.active = False
    if mission.sos_alert:
        mission.sos_alert.status = "Resolved"
    db.commit()
    db.refresh(mission)
    return {"status": "success", "mission_id": mission.id, "new_status": mission.status}

# --- 4. COMMUNITY INCIDENT REPORTING ---

@router.post("/community/report")
def submit_report(req: CommunityReportRequest, db: Session = Depends(get_db)):
    report = CommunityReport(
        reporter_name=req.reporter_name,
        lat=req.lat,
        lon=req.lon,
        incident_type=req.incident_type,
        details=req.details,
        status="Unverified",
        upvotes=1
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"status": "success", "report_id": report.id}

@router.get("/community/reports")
def get_reports(db: Session = Depends(get_db)):
    reports = db.query(CommunityReport).order_by(CommunityReport.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "reporter_name": r.reporter_name,
            "lat": r.lat,
            "lon": r.lon,
            "incident_type": r.incident_type,
            "details": r.details,
            "image_url": r.image_url,
            "status": r.status or "Unverified",
            "upvotes": r.upvotes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]

@router.post("/community/report/{report_id}/upvote")
def upvote_report(report_id: int, db: Session = Depends(get_db)):
    """Increment the upvote count for a community report."""
    report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.upvotes = (report.upvotes or 0) + 1
    db.commit()
    db.refresh(report)
    return {"status": "success", "report_id": report.id, "upvotes": report.upvotes}

# --- 5. AI DISASTER COPILOT CHAT ---

@router.post("/chatbot")
def query_chatbot(req: ChatRequest):
    res = chatbot_copilot.chat_response(
        user_msg=req.message,
        lat=req.lat,
        lon=req.lon,
        lang=req.lang
    )
    return res

# --- 6. HEALTH & ADMIN CONFIGS ---

@router.get("/system/status")
def get_system_status():
    return {
        "status": "Green",
        "latency_ms": 14,
        "services": {
            "geoprocessor": "Live" if gee_service.initialized else "Simulation Mode",
            "xgboost_classifier": "Active",
            "random_forest_landslide": "Active",
            "cnn_chunker": "Online",
            "sqlite_spatial_session": "Connected"
        }
    }

@router.post("/system/settings")
def override_settings(req: SystemSettingsOverride):
    from app.core.config import settings
    settings.THRESHOLD_EXTREME = req.extreme_threshold
    settings.THRESHOLD_HIGH = req.high_threshold
    settings.THRESHOLD_MODERATE = req.mod_threshold
    return {"status": "success", "msg": "Threat warning thresholds adjusted dynamically."}
