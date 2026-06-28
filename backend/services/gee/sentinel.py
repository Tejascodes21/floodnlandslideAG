"""
Sentinel Imagery Processor
===========================
Fetches and processes Sentinel-1 SAR and Sentinel-2 optical imagery.
Implements cloud masking, composite creation, and band extraction.

In simulation mode, generates physically realistic multi-spectral
raster values using deterministic geostatistical wave equations.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from .client import gee_client

logger = logging.getLogger("geoshield.gee.sentinel")


class SentinelProcessor:
    """
    Processes Sentinel-1 (SAR C-band) and Sentinel-2 (MSI optical) imagery.
    
    Sentinel-1 provides all-weather, day-night radar imagery useful for
    flood mapping (specular reflection from water = low backscatter).
    
    Sentinel-2 provides 13 spectral bands at 10-60m resolution for
    vegetation, water body, and land cover classification.
    """
    
    # Sentinel-2 band wavelengths (nm) for reference
    S2_BANDS = {
        "B2_Blue": 490, "B3_Green": 560, "B4_Red": 665,
        "B5_RedEdge1": 705, "B6_RedEdge2": 740, "B7_RedEdge3": 783,
        "B8_NIR": 842, "B8A_NIRnarrow": 865,
        "B11_SWIR1": 1610, "B12_SWIR2": 2190
    }
    
    def fetch_sentinel2_composite(self, lat: float, lon: float,
                                   buffer_m: int = 5000,
                                   days_back: int = 30,
                                   cloud_pct_max: int = 20) -> Dict:
        """
        Fetches a cloud-free Sentinel-2 composite for the area of interest.
        
        Parameters:
            lat, lon: Center coordinates of the AOI
            buffer_m: Buffer radius in meters around the point
            days_back: Number of days to search back for imagery
            cloud_pct_max: Maximum cloud cover percentage filter
            
        Returns:
            Dictionary with band values, metadata, and quality indicators
        """
        ee = gee_client.get_ee()
        
        if ee is not None:
            return self._fetch_s2_live(ee, lat, lon, buffer_m, days_back, cloud_pct_max)
        return self._simulate_s2(lat, lon)
    
    def fetch_sentinel1_sar(self, lat: float, lon: float,
                             buffer_m: int = 5000,
                             days_back: int = 12,
                             orbit_pass: str = "DESCENDING") -> Dict:
        """
        Fetches Sentinel-1 SAR GRD imagery for flood detection.
        
        SAR backscatter characteristics:
          - Open water: Very low VV backscatter (-20 to -25 dB) due to specular reflection
          - Urban areas: High backscatter (-5 to -10 dB) from double-bounce
          - Vegetation: Moderate backscatter (-10 to -15 dB) from volume scattering
          - Flooded vegetation: Modified backscatter pattern detectable via VH polarization
        """
        ee = gee_client.get_ee()
        
        if ee is not None:
            return self._fetch_s1_live(ee, lat, lon, buffer_m, days_back, orbit_pass)
        return self._simulate_s1(lat, lon)
    
    def _fetch_s2_live(self, ee, lat, lon, buffer_m, days_back, cloud_pct_max):
        """Real GEE Sentinel-2 fetch with cloud masking."""
        import datetime
        
        aoi = ee.Geometry.Point(lon, lat).buffer(buffer_m)
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days_back)
        
        # Cloud mask function using QA60 band
        def mask_clouds(image):
            qa = image.select('QA60')
            cloud_mask = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
            return image.updateMask(cloud_mask).divide(10000)
        
        collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filterBounds(aoi)
                       .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_pct_max))
                       .map(mask_clouds)
                       .median())
        
        bands = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
        values = collection.select(bands).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=10, maxPixels=1e9
        ).getInfo()
        
        return {
            "source": "Sentinel-2 SR Harmonized (GEE Live)",
            "bands": values,
            "blue": values.get("B2", 0), "green": values.get("B3", 0),
            "red": values.get("B4", 0), "nir": values.get("B8", 0),
            "swir1": values.get("B11", 0), "swir2": values.get("B12", 0),
            "cloud_mask_applied": True,
            "scene_count": 1
        }
    
    def _fetch_s1_live(self, ee, lat, lon, buffer_m, days_back, orbit_pass):
        """Real GEE Sentinel-1 SAR fetch."""
        import datetime
        
        aoi = ee.Geometry.Point(lon, lat).buffer(buffer_m)
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days_back)
        
        collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                       .filterBounds(aoi)
                       .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                       .filter(ee.Filter.eq('instrumentMode', 'IW'))
                       .filter(ee.Filter.eq('orbitProperties_pass', orbit_pass))
                       .select(['VV', 'VH'])
                       .median())
        
        values = collection.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=10, maxPixels=1e9
        ).getInfo()
        
        return {
            "source": "Sentinel-1 GRD (GEE Live)",
            "vv_db": values.get("VV", -12.0),
            "vh_db": values.get("VH", -18.0),
            "polarization": "VV+VH",
            "orbit": orbit_pass,
            "instrument_mode": "IW"
        }
    
    def _simulate_s2(self, lat: float, lon: float) -> Dict:
        """
        High-fidelity Sentinel-2 simulation using deterministic spectral models.
        
        Physical basis:
          - Water absorbs NIR strongly → low B8, high B2/B3
          - Vegetation reflects NIR → high B8, low B4
          - Bare soil has flat spectral response
          - Urban areas reflect moderately across all bands
        """
        seed = int(abs(lat * 1000) + abs(lon * 1000)) % 10000
        rng = np.random.RandomState(seed)
        
        # Terrain-based land cover estimation
        h_wave = np.sin(lat * 1.5) * np.cos(lon * 1.5)
        elevation_proxy = 300 + h_wave * 450
        water_proximity = max(0, np.sin(lat * 25.0) * np.cos(lon * 25.0))
        veg_density = 0.4 + (0.5 if elevation_proxy < 600 else 0.1)
        
        # Spectral reflectance model (surface reflectance units 0-1)
        if water_proximity > 0.4:
            # Water-dominated pixel
            blue = float(np.clip(0.08 + rng.normal(0, 0.01), 0.02, 0.15))
            green = float(np.clip(0.06 + rng.normal(0, 0.01), 0.02, 0.12))
            red = float(np.clip(0.03 + rng.normal(0, 0.005), 0.01, 0.08))
            nir = float(np.clip(0.015 + rng.normal(0, 0.005), 0.005, 0.04))
            swir1 = float(np.clip(0.005 + rng.normal(0, 0.002), 0.001, 0.02))
            swir2 = float(np.clip(0.003 + rng.normal(0, 0.001), 0.001, 0.01))
        elif veg_density > 0.6:
            # Vegetation-dominated pixel
            blue = float(np.clip(0.03 + rng.normal(0, 0.005), 0.01, 0.06))
            green = float(np.clip(0.07 + rng.normal(0, 0.01), 0.03, 0.12))
            red = float(np.clip(0.035 + rng.normal(0, 0.008), 0.01, 0.07))
            nir = float(np.clip(0.35 + veg_density * 0.2 + rng.normal(0, 0.03), 0.15, 0.55))
            swir1 = float(np.clip(0.15 + rng.normal(0, 0.02), 0.05, 0.25))
            swir2 = float(np.clip(0.08 + rng.normal(0, 0.015), 0.03, 0.15))
        else:
            # Bare soil / urban
            blue = float(np.clip(0.10 + rng.normal(0, 0.02), 0.04, 0.18))
            green = float(np.clip(0.12 + rng.normal(0, 0.02), 0.05, 0.20))
            red = float(np.clip(0.15 + rng.normal(0, 0.025), 0.06, 0.25))
            nir = float(np.clip(0.20 + rng.normal(0, 0.03), 0.08, 0.35))
            swir1 = float(np.clip(0.22 + rng.normal(0, 0.03), 0.10, 0.35))
            swir2 = float(np.clip(0.18 + rng.normal(0, 0.025), 0.08, 0.30))
        
        red_edge1 = float((red + nir) / 2 * 0.85)
        red_edge2 = float((red + nir) / 2 * 0.92)
        red_edge3 = float((red + nir) / 2 * 0.97)
        nir_narrow = float(nir * 0.98)
        
        return {
            "source": "Sentinel-2 (Simulated — Geostatistical Spectral Model)",
            "bands": {
                "B2": blue, "B3": green, "B4": red,
                "B5": red_edge1, "B6": red_edge2, "B7": red_edge3,
                "B8": nir, "B8A": nir_narrow,
                "B11": swir1, "B12": swir2
            },
            "blue": blue, "green": green, "red": red,
            "nir": nir, "swir1": swir1, "swir2": swir2,
            "cloud_mask_applied": True,
            "scene_count": 3
        }
    
    def _simulate_s1(self, lat: float, lon: float) -> Dict:
        """
        High-fidelity SAR simulation.
        
        Physical basis:
          - VV polarization: Sensitive to surface roughness and moisture
          - VH polarization: Sensitive to volume scattering (vegetation)
          - Water surfaces: VV ≈ -20 to -25 dB, VH ≈ -28 to -33 dB
          - Urban: VV ≈ -5 to -10 dB, VH ≈ -12 to -18 dB
          - Forest: VV ≈ -8 to -14 dB, VH ≈ -14 to -20 dB
        """
        seed = int(abs(lat * 1000) + abs(lon * 1000)) % 10000
        rng = np.random.RandomState(seed)
        
        h_wave = np.sin(lat * 1.5) * np.cos(lon * 1.5)
        elevation_proxy = 300 + h_wave * 450
        water_signal = np.sin(lat * 25.0) * np.cos(lon * 25.0)
        slope_proxy = abs(np.cos(lat * 2.0) * np.sin(lon * 2.0) * 35)
        
        if water_signal > 0.3:
            # Open water — specular reflection
            vv = float(np.clip(-22.0 + rng.normal(0, 1.5), -27, -17))
            vh = float(np.clip(-30.0 + rng.normal(0, 1.5), -35, -25))
        elif slope_proxy > 20:
            # Rough terrain / mountains
            vv = float(np.clip(-8.0 + (slope_proxy / 45) * 4 + rng.normal(0, 1.2), -15, -3))
            vh = float(np.clip(-15.0 + (slope_proxy / 45) * 3 + rng.normal(0, 1.0), -22, -10))
        else:
            # Mixed land cover
            vv = float(np.clip(-12.0 + rng.normal(0, 2.0), -18, -6))
            vh = float(np.clip(-19.0 + rng.normal(0, 1.8), -25, -13))
        
        return {
            "source": "Sentinel-1 GRD (Simulated — SAR Backscatter Model)",
            "vv_db": round(vv, 2),
            "vh_db": round(vh, 2),
            "polarization": "VV+VH",
            "orbit": "DESCENDING",
            "instrument_mode": "IW"
        }


# Module-level singleton
sentinel_processor = SentinelProcessor()
