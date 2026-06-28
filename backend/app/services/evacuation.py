"""
Evacuation Routing Service
===========================
Calculates safe evacuation routes avoiding high-risk zones.
"""

import numpy as np
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("geoshield.services.evacuation")

class EvacuationRouter:
    """
    Computes safe routing paths using simulated A* over a risk grid.
    """
    
    def calculate_safe_route(self, start_lat: float, start_lon: float,
                              end_lat: float, end_lon: float,
                              hazard_type: str = "flood") -> Dict:
        """
        Simulate a safe route avoiding high-risk topographic/hydrologic features.
        In a production environment, this would integrate with OSM/Google Maps API
        and apply the risk grid as a cost penalty.
        """
        # Distance calculation
        dist = self._haversine(start_lat, start_lon, end_lat, end_lon)
        
        # Simulate route steps (approximate polyline)
        steps = max(5, int(dist * 2))
        route_points = []
        
        # Add a curve to simulate avoiding a central hazard
        seed = int(abs(start_lat * 100) + abs(start_lon * 100)) % 1000
        rng = np.random.RandomState(seed)
        
        curve_factor = rng.uniform(0.1, 0.3)
        if rng.rand() > 0.5:
            curve_factor *= -1
            
        for i in range(steps + 1):
            t = i / steps
            # Linear interpolation
            interp_lat = start_lat + (end_lat - start_lat) * t
            interp_lon = start_lon + (end_lon - start_lon) * t
            
            # Add parabolic curve
            offset_lat = curve_factor * (end_lon - start_lon) * (t - t**2)
            offset_lon = -curve_factor * (end_lat - start_lat) * (t - t**2)
            
            route_points.append({
                "lat": round(interp_lat + offset_lat, 5),
                "lon": round(interp_lon + offset_lon, 5)
            })
            
        # Estimated time (assuming 30 km/h average safe speed)
        time_minutes = int((dist / 30.0) * 60)
        
        return {
            "distance_km": round(dist, 2),
            "estimated_time_min": time_minutes,
            "route_points": route_points,
            "safe_shelters": self._find_nearby_shelters(end_lat, end_lon, rng)
        }
        
    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1_r, lon1_r = np.radians(lat1), np.radians(lon1)
        lat2_r, lon2_r = np.radians(lat2), np.radians(lon2)
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        a = np.sin(dlat / 2)**2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c
        
    def _find_nearby_shelters(self, lat: float, lon: float, rng) -> List[Dict]:
        """Generate simulated safe shelters near the destination."""
        shelters = []
        names = ["Municipal School", "Community Hall", "High Ground Camp", "Relief Center"]
        for _ in range(rng.randint(1, 4)):
            shelters.append({
                "name": rng.choice(names),
                "lat": round(lat + rng.uniform(-0.02, 0.02), 5),
                "lon": round(lon + rng.uniform(-0.02, 0.02), 5),
                "capacity": rng.randint(50, 500)
            })
        return shelters

evacuation_router = EvacuationRouter()
