"""
GeoShield AI — API Endpoints Package
====================================
"""
from fastapi import APIRouter

from .predictions import router as predictions_router
from .realtime import router as realtime_router
from .damage import router as damage_router
from .gis import router as gis_router

# Core router to be included in main.py
api_router = APIRouter()

api_router.include_router(predictions_router, prefix="/predict", tags=["predictions"])
api_router.include_router(realtime_router, prefix="/realtime", tags=["realtime"])
api_router.include_router(damage_router, prefix="/damage", tags=["damage"])
api_router.include_router(gis_router, prefix="/gis", tags=["gis"])
