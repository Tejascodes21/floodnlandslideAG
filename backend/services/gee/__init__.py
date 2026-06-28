"""
GeoShield AI — Google Earth Engine Integration Pipeline
=======================================================
Production-grade GEE module for Sentinel-1/2 imagery processing,
spectral indices, terrain analysis, and geospatial feature extraction.

Supports dual-mode operation:
  - Real GEE SDK mode (when ee is authenticated)
  - High-fidelity simulation mode (deterministic geostatistical fallback)
"""

from .client import GEEClient, gee_client
from .pipeline import GEEPipeline, gee_pipeline

__all__ = ["GEEClient", "gee_client", "GEEPipeline", "gee_pipeline"]
