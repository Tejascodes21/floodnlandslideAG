"""
AOI Preprocessing & Coordinate Utilities
==========================================
Converts lat/lon coordinates to geometries, builds Areas of Interest,
handles coordinate system transformations, and preprocesses imagery
for downstream model consumption.
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("geoshield.gee.preprocessing")


class GeoPreprocessor:
    """
    Handles coordinate transformations and AOI operations.
    """
    
    @staticmethod
    def create_aoi(lat: float, lon: float, buffer_km: float = 5.0) -> Dict:
        """
        Creates an Area of Interest bounding box centered on coordinates.
        
        Returns:
            Dict with center, bbox corners, area, and geometry metadata
        """
        # Approximate degree offsets (1° lat ≈ 111km, 1° lon varies with latitude)
        lat_offset = buffer_km / 111.0
        lon_offset = buffer_km / (111.0 * np.cos(np.radians(lat)))
        
        bbox = {
            "min_lat": round(lat - lat_offset, 6),
            "max_lat": round(lat + lat_offset, 6),
            "min_lon": round(lon - lon_offset, 6),
            "max_lon": round(lon + lon_offset, 6)
        }
        
        area_km2 = (2 * buffer_km) ** 2  # Approximate square area
        
        return {
            "center": {"lat": lat, "lon": lon},
            "buffer_km": buffer_km,
            "bbox": bbox,
            "area_km2": round(area_km2, 2),
            "corners": [
                [bbox["min_lat"], bbox["min_lon"]],
                [bbox["min_lat"], bbox["max_lon"]],
                [bbox["max_lat"], bbox["max_lon"]],
                [bbox["max_lat"], bbox["min_lon"]]
            ],
            "crs": "EPSG:4326"
        }
    
    @staticmethod
    def create_grid(lat: float, lon: float, grid_size: int = 8,
                    cell_size_m: float = 500) -> List[Dict]:
        """
        Creates an analysis grid of cells around the center point.
        Used for spatial risk distribution heatmaps.
        
        Parameters:
            grid_size: Number of cells per axis (grid_size x grid_size)
            cell_size_m: Size of each cell in meters
        """
        cell_deg_lat = cell_size_m / 111000
        cell_deg_lon = cell_size_m / (111000 * np.cos(np.radians(lat)))
        
        half = grid_size / 2
        cells = []
        
        for r in range(grid_size):
            for c in range(grid_size):
                cell_lat = lat + (r - half + 0.5) * cell_deg_lat
                cell_lon = lon + (c - half + 0.5) * cell_deg_lon
                cells.append({
                    "row": r, "col": c,
                    "lat": round(cell_lat, 6),
                    "lon": round(cell_lon, 6),
                    "bounds": {
                        "min_lat": round(cell_lat - cell_deg_lat / 2, 6),
                        "max_lat": round(cell_lat + cell_deg_lat / 2, 6),
                        "min_lon": round(cell_lon - cell_deg_lon / 2, 6),
                        "max_lon": round(cell_lon + cell_deg_lon / 2, 6)
                    }
                })
        
        return cells
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float,
                            lat2: float, lon2: float) -> float:
        """
        Calculates great-circle distance between two points in km.
        Uses the Haversine formula.
        """
        R = 6371.0  # Earth radius in km
        
        lat1_r, lon1_r = np.radians(lat1), np.radians(lon1)
        lat2_r, lon2_r = np.radians(lat2), np.radians(lon2)
        
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        
        return round(R * c, 3)
    
    @staticmethod
    def normalize_feature_vector(features: Dict, feature_cols: List[str]) -> List[float]:
        """
        Assembles a feature vector from a dictionary in the correct column order
        for ML model input.
        """
        vector = []
        for col in feature_cols:
            val = features.get(col, 0.0)
            vector.append(float(val) if val is not None else 0.0)
        return vector
    
    @staticmethod
    def classify_climate_zone(lat: float, lon: float) -> str:
        """Rough climate zone classification for rainfall pattern estimation."""
        abs_lat = abs(lat)
        if abs_lat < 10:
            return "Tropical_Wet"
        elif abs_lat < 23.5:
            if 68 < lon < 97:
                return "Tropical_Monsoon"
            return "Tropical_Dry"
        elif abs_lat < 35:
            return "Subtropical"
        elif abs_lat < 55:
            return "Temperate"
        else:
            return "Polar"
    
    @staticmethod
    def estimate_soil_type(elevation: float, slope: float, ndvi: float) -> Tuple[str, int]:
        """
        Estimates soil type and encoded value from terrain indicators.
        
        Returns:
            (soil_type_name, encoded_value)
        """
        if elevation < 50 and slope < 3:
            return ("Alluvial Clay", 0)
        elif elevation < 200 and ndvi > 0.5:
            return ("Laterite", 1)
        elif slope > 25:
            return ("Rocky/Lithosol", 2)
        elif ndvi > 0.6 and elevation < 800:
            return ("Forest Loam", 3)
        elif elevation > 1200:
            return ("Alpine Regosol", 4)
        elif ndvi < 0.2:
            return ("Sandy/Arid", 5)
        else:
            return ("Mixed Sedimentary", 6)


preprocessor = GeoPreprocessor()
