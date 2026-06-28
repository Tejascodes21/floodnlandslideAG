"""
Damage Assessment Service
==========================
Estimates infrastructure damage, population affected, and economic
losses based on hazard severity and geospatial location data.
"""

import numpy as np
import logging
from typing import Dict, List

logger = logging.getLogger("geoshield.services.damage")

class DamageAssessor:
    """
    Estimates multi-sectoral damage post-disaster.
    """
    
    def estimate_impact(self, lat: float, lon: float, hazard_type: str, severity: float, radius_km: float = 5.0) -> Dict:
        """
        Estimate infrastructure and population impact within a radius.
        Uses probabilistic models based on severity.
        """
        seed = int(abs(lat * 100) + abs(lon * 100)) % 1000
        rng = np.random.RandomState(seed)
        
        # Base population density proxy
        pop_density = rng.gamma(2, 500) # people per sq km
        area = np.pi * (radius_km ** 2)
        total_pop = int(pop_density * area)
        
        # Damage scaling factor based on severity (0-1)
        scale = max(0, min(1, severity))
        
        if hazard_type == "flood":
            # Floods impact wider areas, more population, but less structural collapse
            affected_pop = int(total_pop * (scale * 0.8 + rng.uniform(0, 0.1)))
            buildings_damaged = int(affected_pop * rng.uniform(0.1, 0.3) * scale)
            roads_blocked_km = round(area * scale * rng.uniform(0.2, 0.8), 2)
            economic_loss_usd = buildings_damaged * rng.uniform(5000, 20000)
            
        elif hazard_type == "landslide":
            # Landslides are localized but highly destructive structurally
            affected_pop = int(total_pop * (scale * 0.3 + rng.uniform(0, 0.05)))
            buildings_damaged = int(affected_pop * rng.uniform(0.6, 0.9) * scale)
            roads_blocked_km = round(radius_km * scale * rng.uniform(0.5, 1.5), 2)
            economic_loss_usd = buildings_damaged * rng.uniform(15000, 50000)
            
        else:
            affected_pop = 0
            buildings_damaged = 0
            roads_blocked_km = 0.0
            economic_loss_usd = 0
            
        return {
            "hazard_type": hazard_type,
            "severity_score": round(scale, 2),
            "estimated_impact": {
                "population_affected": affected_pop,
                "buildings_damaged": buildings_damaged,
                "roads_blocked_km": roads_blocked_km,
                "economic_loss_usd": int(economic_loss_usd)
            },
            "critical_infrastructure_at_risk": self._simulate_critical_infra(rng, scale)
        }
        
    def _simulate_critical_infra(self, rng, scale: float) -> List[Dict]:
        """Simulate hospitals, schools, power grids at risk."""
        infra = []
        if rng.rand() < (0.3 + scale * 0.2):
            infra.append({"type": "Hospital", "status": "Compromised" if scale > 0.7 else "At Risk"})
        if rng.rand() < (0.5 + scale * 0.3):
            infra.append({"type": "Power Substation", "status": "Offline" if scale > 0.6 else "Vulnerable"})
        if rng.rand() < 0.6:
            infra.append({"type": "School", "status": "Used as Shelter" if scale > 0.4 else "Closed"})
        return infra

damage_assessor = DamageAssessor()
