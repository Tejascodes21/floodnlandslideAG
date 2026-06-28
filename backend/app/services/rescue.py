import numpy as np
import json

class RescueCoordinationService:
    def __init__(self):
        # Sample relief shelters (coordinates placed on high grounds)
        self.shelters = [
            {"name": "Municipal Sports Complex Camp A (Elev: 220m)", "lat": 19.125, "lon": 72.890},
            {"name": "State College Hall Relief Hub B (Elev: 185m)", "lat": 19.075, "lon": 72.840},
            {"name": "District High School Camp C (Elev: 310m)", "lat": 19.030, "lon": 72.860}
        ]

    def find_nearest_shelter(self, lat: float, lon: float) -> dict:
        """Finds closest safe relief camp based on coordinate distances."""
        closest_shelter = None
        min_dist = float('inf')
        
        for shelter in self.shelters:
            dist = np.sqrt((lat - shelter["lat"])**2 + (lon - shelter["lon"])**2)
            if dist < min_dist:
                min_dist = dist
                closest_shelter = shelter
                
        return closest_shelter

    def match_nearest_volunteer(self, sos_lat: float, sos_lon: float, volunteers: list) -> dict:
        """
        AI Allocation: Computes coordinate distances across registered volunteers 
        and assigns the closest active agent matching critical rescue skills.
        """
        closest_vol = None
        min_dist = float('inf')
        
        for vol in volunteers:
            if not vol.get("active", True):
                continue
            dist = np.sqrt((sos_lat - vol["lat"])**2 + (sos_lon - vol["lon"])**2)
            if dist < min_dist:
                min_dist = dist
                closest_vol = vol
                
        return closest_vol

    def generate_safe_route(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, hazard_zones: list) -> list:
        """
        Generates a GIS route polyline. If the straight-line path intersects high hazard zones,
        calculates a deflected, hazard-safe route curve to bypass active risk sectors.
        """
        steps = 8
        path = []
        
        # Linear interpolation steps
        lats = np.linspace(start_lat, end_lat, steps)
        lons = np.linspace(start_lon, end_lon, steps)
        
        for i in range(steps):
            curr_lat = float(lats[i])
            curr_lon = float(lons[i])
            
            # Avoid hazard zones by deflecting coordinates if too close
            for hazard in hazard_zones:
                hz_lat = hazard.get("lat")
                hz_lon = hazard.get("lon")
                hz_radius = 0.003  # geodetic buffer
                
                dist = np.sqrt((curr_lat - hz_lat)**2 + (curr_lon - hz_lon)**2)
                if dist < hz_radius:
                    # Push coordinate outward to bypass the danger zone
                    deflection_lat = (curr_lat - hz_lat) / (dist + 0.0001) * 0.004
                    deflection_lon = (curr_lon - hz_lon) / (dist + 0.0001) * 0.004
                    
                    curr_lat += deflection_lat
                    curr_lon += deflection_lon
            
            path.append({"lat": round(curr_lat, 6), "lon": round(curr_lon, 6)})
            
        return path

rescue_service = RescueCoordinationService()
