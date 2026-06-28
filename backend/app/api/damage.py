"""
Damage Assessment API Endpoint
===============================
Provides damage estimation and post-disaster analytics.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

from app.services.damage_assessment import damage_assessor

router = APIRouter()

class DamageRequest(BaseModel):
    lat: float
    lon: float
    hazard_type: str # 'flood' or 'landslide'
    severity: float # 0.0 to 1.0
    radius_km: Optional[float] = 5.0

@router.post("/estimate")
async def estimate_damage(request: DamageRequest):
    """
    Estimates infrastructure damage, population affected, and economic loss.
    """
    if request.hazard_type not in ["flood", "landslide"]:
        raise HTTPException(status_code=400, detail="Invalid hazard type. Must be 'flood' or 'landslide'.")
        
    try:
        impact = damage_assessor.estimate_impact(
            request.lat, request.lon, request.hazard_type, request.severity, request.radius_km
        )
        return {"status": "success", "data": impact}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
