"""
Spectral Index Calculator
=========================
Computes vegetation, water, and moisture spectral indices from
Sentinel-2 band data. All indices are standard remote sensing 
formulations used in flood/landslide hazard mapping.
"""

import numpy as np
import logging
from typing import Dict, Optional
from .client import gee_client

logger = logging.getLogger("geoshield.gee.indices")


class SpectralIndexCalculator:
    """
    Calculates standardized spectral indices from multi-band imagery.
    
    Supported indices:
      - NDWI:  Normalized Difference Water Index (McFeeters, 1996)
      - MNDWI: Modified NDWI using SWIR (Xu, 2006)  
      - NDVI:  Normalized Difference Vegetation Index (Rouse, 1974)
      - EVI:   Enhanced Vegetation Index (Huete, 2002)
      - NDMI:  Normalized Difference Moisture Index
      - BSI:   Bare Soil Index
      - SAVI:  Soil Adjusted Vegetation Index
    """
    
    @staticmethod
    def ndwi(green: float, nir: float) -> float:
        """
        NDWI = (Green - NIR) / (Green + NIR)
        
        Range: -1 to +1
        Water: > 0.0 (strong water signal > 0.3)
        Vegetation: < 0.0
        
        Used for: Surface water delineation, flood mapping
        Reference: McFeeters (1996) — "The use of NDWI for delineating open water features"
        """
        if abs(green + nir) < 1e-10:
            return 0.0
        return float(np.clip((green - nir) / (green + nir), -1.0, 1.0))
    
    @staticmethod
    def mndwi(green: float, swir1: float) -> float:
        """
        MNDWI = (Green - SWIR1) / (Green + SWIR1)
        
        Enhanced water detection, reduces false positives from built-up areas.
        Reference: Xu (2006) — "Modification of NDWI to enhance open water features"
        """
        if abs(green + swir1) < 1e-10:
            return 0.0
        return float(np.clip((green - swir1) / (green + swir1), -1.0, 1.0))
    
    @staticmethod
    def ndvi(nir: float, red: float) -> float:
        """
        NDVI = (NIR - Red) / (NIR + Red)
        
        Range: -1 to +1
        Dense vegetation: > 0.5
        Sparse vegetation: 0.2-0.5
        Bare soil: 0.0-0.2
        Water/Snow: < 0.0
        
        Used for: Vegetation health, landslide-prone barren slope detection
        Reference: Rouse et al. (1974)
        """
        if abs(nir + red) < 1e-10:
            return 0.0
        return float(np.clip((nir - red) / (nir + red), -1.0, 1.0))
    
    @staticmethod
    def evi(nir: float, red: float, blue: float, G: float = 2.5,
            C1: float = 6.0, C2: float = 7.5, L: float = 1.0) -> float:
        """
        EVI = G * (NIR - Red) / (NIR + C1*Red - C2*Blue + L)
        
        Enhanced vegetation index, corrects for atmospheric and
        canopy background effects. Better for high-biomass regions.
        Reference: Huete et al. (2002)
        """
        denom = nir + C1 * red - C2 * blue + L
        if abs(denom) < 1e-10:
            return 0.0
        return float(np.clip(G * (nir - red) / denom, -1.0, 1.0))
    
    @staticmethod
    def ndmi(nir: float, swir1: float) -> float:
        """
        NDMI = (NIR - SWIR1) / (NIR + SWIR1)
        
        Measures vegetation water content / canopy moisture stress.
        High values indicate wet vegetation (pre-landslide soil saturation).
        """
        if abs(nir + swir1) < 1e-10:
            return 0.0
        return float(np.clip((nir - swir1) / (nir + swir1), -1.0, 1.0))
    
    @staticmethod
    def bsi(blue: float, red: float, nir: float, swir1: float) -> float:
        """
        BSI = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
        
        Bare Soil Index — identifies exposed soil (landslide scars, deforested slopes).
        """
        num = (swir1 + red) - (nir + blue)
        den = (swir1 + red) + (nir + blue)
        if abs(den) < 1e-10:
            return 0.0
        return float(np.clip(num / den, -1.0, 1.0))
    
    @staticmethod
    def savi(nir: float, red: float, L: float = 0.5) -> float:
        """
        SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)
        
        Soil-adjusted vegetation index, reduces soil brightness influence.
        """
        denom = nir + red + L
        if abs(denom) < 1e-10:
            return 0.0
        return float(np.clip(((nir - red) / denom) * (1 + L), -1.0, 1.0))
    
    def compute_all(self, bands: Dict[str, float]) -> Dict[str, float]:
        """
        Computes all spectral indices from a Sentinel-2 band dictionary.
        
        Parameters:
            bands: Dict with keys B2 (blue), B3 (green), B4 (red), 
                   B8 (nir), B11 (swir1), B12 (swir2)
        
        Returns:
            Dictionary of all index values
        """
        blue = bands.get("B2", bands.get("blue", 0.05))
        green = bands.get("B3", bands.get("green", 0.08))
        red = bands.get("B4", bands.get("red", 0.06))
        nir = bands.get("B8", bands.get("nir", 0.30))
        swir1 = bands.get("B11", bands.get("swir1", 0.15))
        swir2 = bands.get("B12", bands.get("swir2", 0.10))
        
        return {
            "ndwi": round(self.ndwi(green, nir), 4),
            "mndwi": round(self.mndwi(green, swir1), 4),
            "ndvi": round(self.ndvi(nir, red), 4),
            "evi": round(self.evi(nir, red, blue), 4),
            "ndmi": round(self.ndmi(nir, swir1), 4),
            "bsi": round(self.bsi(blue, red, nir, swir1), 4),
            "savi": round(self.savi(nir, red), 4)
        }
    
    def compute_from_coords(self, lat: float, lon: float) -> Dict[str, float]:
        """Compute indices directly from coordinates using simulated S2 bands."""
        from .sentinel import sentinel_processor
        s2_data = sentinel_processor.fetch_sentinel2_composite(lat, lon)
        bands = s2_data.get("bands", s2_data)
        result = self.compute_all(bands)
        result["source"] = s2_data.get("source", "Unknown")
        return result


# Module-level singleton
index_calculator = SpectralIndexCalculator()
