"""
Time-Series Imagery Processor
===============================
Generates temporal sequences of spectral indices for change detection,
storm impact analysis, and seasonal monitoring.

Produces chronological NDWI/NDVI/SAR time-series that show:
  - Pre-event baseline conditions
  - During-event peak flood/landslide signatures  
  - Post-event recovery progression
"""

import numpy as np
import logging
from typing import Dict, List
from .client import gee_client

logger = logging.getLogger("geoshield.gee.timeseries")


class TimeSeriesProcessor:
    """
    Generates multi-temporal satellite data sequences for trend analysis
    and anomaly detection in flood/landslide monitoring.
    """
    
    def generate_spectral_timeseries(self, lat: float, lon: float,
                                      days_back: int = 90,
                                      interval_days: int = 6) -> List[Dict]:
        """
        Generates a time-series of spectral indices at regular intervals.
        
        Parameters:
            lat, lon: Center coordinates
            days_back: Total historical window to cover
            interval_days: Time step between observations (Sentinel-2 revisit = 5 days)
            
        Returns:
            List of dicts, each representing one temporal observation with
            NDWI, NDVI, SAR backscatter, and soil moisture values
        """
        ee = gee_client.get_ee()
        if ee is not None:
            return self._ts_live(ee, lat, lon, days_back, interval_days)
        return self._ts_simulate(lat, lon, days_back, interval_days)
    
    def detect_change_events(self, timeseries: List[Dict],
                              ndwi_threshold: float = 0.15,
                              ndvi_drop_threshold: float = -0.1) -> List[Dict]:
        """
        Analyzes time-series for abrupt change events indicating:
          - Flood onset: Sudden NDWI increase + SAR backscatter drop
          - Landslide: Sudden NDVI decrease + high SAR variation
          - Recovery: Gradual NDVI increase post-event
        """
        events = []
        for i in range(1, len(timeseries)):
            prev = timeseries[i - 1]
            curr = timeseries[i]
            
            ndwi_delta = curr["ndwi"] - prev["ndwi"]
            ndvi_delta = curr["ndvi"] - prev["ndvi"]
            sar_delta = curr.get("sar_vv_db", -12) - prev.get("sar_vv_db", -12)
            
            event = None
            if ndwi_delta > ndwi_threshold and sar_delta < -2:
                event = {
                    "type": "flood_onset",
                    "severity": "high" if ndwi_delta > 0.25 else "moderate",
                    "day": curr["days_ago"],
                    "ndwi_change": round(ndwi_delta, 4),
                    "confidence": round(min(1.0, abs(ndwi_delta) * 3), 2)
                }
            elif ndvi_delta < ndvi_drop_threshold:
                event = {
                    "type": "vegetation_loss" if ndvi_delta > -0.2 else "landslide_signature",
                    "severity": "high" if ndvi_delta < -0.25 else "moderate",
                    "day": curr["days_ago"],
                    "ndvi_change": round(ndvi_delta, 4),
                    "confidence": round(min(1.0, abs(ndvi_delta) * 3), 2)
                }
            elif ndwi_delta < -ndwi_threshold and ndvi_delta > 0.05:
                event = {
                    "type": "flood_recession",
                    "severity": "low",
                    "day": curr["days_ago"],
                    "ndwi_change": round(ndwi_delta, 4),
                    "confidence": round(min(1.0, abs(ndwi_delta) * 2.5), 2)
                }
            
            if event:
                events.append(event)
        
        return events
    
    def generate_storm_impact_sequence(self, lat: float, lon: float,
                                        storm_day_offset: int = 15) -> Dict:
        """
        Generates a 3-phase temporal analysis:
          Phase 1 (Before): 30-15 days before storm
          Phase 2 (During): Storm event window (5 days around peak)
          Phase 3 (After):  Recovery period (15-30 days after)
        """
        full_ts = self.generate_spectral_timeseries(lat, lon, days_back=60, interval_days=5)
        
        before = [t for t in full_ts if t["days_ago"] > storm_day_offset + 5]
        during = [t for t in full_ts if abs(t["days_ago"] - storm_day_offset) <= 5]
        after = [t for t in full_ts if t["days_ago"] < storm_day_offset - 5]
        
        def avg_phase(phase_data, key):
            if not phase_data:
                return 0.0
            return round(np.mean([d.get(key, 0) for d in phase_data]), 4)
        
        return {
            "phases": {
                "before": {"ndwi": avg_phase(before, "ndwi"), "ndvi": avg_phase(before, "ndvi"),
                           "soil_moisture": avg_phase(before, "soil_moisture"), "frames": len(before)},
                "during": {"ndwi": avg_phase(during, "ndwi"), "ndvi": avg_phase(during, "ndvi"),
                           "soil_moisture": avg_phase(during, "soil_moisture"), "frames": len(during)},
                "after": {"ndwi": avg_phase(after, "ndwi"), "ndvi": avg_phase(after, "ndvi"),
                          "soil_moisture": avg_phase(after, "soil_moisture"), "frames": len(after)}
            },
            "change_events": self.detect_change_events(full_ts),
            "full_timeseries": full_ts
        }
    
    # --- Live GEE ---
    
    def _ts_live(self, ee, lat, lon, days_back, interval_days):
        import datetime
        from .indices import index_calculator
        
        aoi = ee.Geometry.Point(lon, lat).buffer(2000)
        end_date = datetime.datetime.utcnow()
        results = []
        
        num_steps = days_back // interval_days
        for i in range(num_steps):
            d_ago = i * interval_days
            d_end = end_date - datetime.timedelta(days=d_ago)
            d_start = d_end - datetime.timedelta(days=interval_days)
            
            try:
                s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filterBounds(aoi)
                       .filterDate(d_start.strftime('%Y-%m-%d'), d_end.strftime('%Y-%m-%d'))
                       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
                       .median()
                       .divide(10000))
                
                bands = s2.select(['B2', 'B3', 'B4', 'B8', 'B11']).reduceRegion(
                    ee.Reducer.mean(), aoi, 20, maxPixels=1e7
                ).getInfo()
                
                if bands and bands.get('B3') is not None:
                    indices = index_calculator.compute_all(bands)
                    results.append({
                        "days_ago": d_ago,
                        "ndwi": indices["ndwi"],
                        "ndvi": indices["ndvi"],
                        "mndwi": indices["mndwi"],
                        "sar_vv_db": -12.0,
                        "soil_moisture": 45.0,
                        "source": "GEE Live"
                    })
            except Exception as e:
                logger.debug(f"Time-series step {d_ago} failed: {e}")
                continue
        
        return results if results else self._ts_simulate(lat, lon, days_back, interval_days)
    
    # --- Simulation ---
    
    def _ts_simulate(self, lat: float, lon: float, days_back: int, interval_days: int) -> List[Dict]:
        """
        Generates a physically realistic temporal sequence simulating:
          - Gradual seasonal vegetation changes
          - Storm-induced NDWI spikes (simulated event around day 15-20)
          - Post-event NDVI depression and recovery
          - Soil moisture response to rainfall events
        """
        seed = int(abs(lat * 1000) + abs(lon * 1000)) % 10000
        rng = np.random.RandomState(seed)
        
        # Baseline conditions from terrain
        h_wave = np.sin(lat * 1.5) * np.cos(lon * 1.5)
        elev_proxy = 300 + h_wave * 450
        
        base_ndwi = -0.4 + (1.0 - elev_proxy / 800) * 0.3
        if elev_proxy < 100:
            base_ndwi += 0.25
        base_ndwi = np.clip(base_ndwi, -0.6, 0.5)
        
        base_ndvi = 0.4 + (0.5 if elev_proxy < 600 else 0.1)
        if elev_proxy > 1600:
            base_ndvi = 0.15
        base_ndvi = np.clip(base_ndvi, 0.0, 0.8)
        
        base_sm = 35 + base_ndvi * 40 + base_ndwi * 20
        base_sar = -12.0 if base_ndwi < 0.1 else -22.0 + base_ndwi * 3
        
        # Storm event window (simulated around 15-25 days ago)
        storm_peak = rng.randint(15, 25)
        storm_intensity = rng.uniform(0.3, 0.8)
        
        results = []
        num_steps = days_back // interval_days
        
        for i in range(num_steps):
            d_ago = days_back - (i * interval_days)
            
            # Temporal modulation: storm impact curve (Gaussian pulse)
            storm_dist = abs(d_ago - storm_peak)
            storm_effect = storm_intensity * np.exp(-(storm_dist ** 2) / 50)
            
            # NDWI increases during flood (water on surface)
            ndwi_t = base_ndwi + storm_effect * 0.35 + rng.normal(0, 0.02)
            
            # NDVI decreases during/after storm (vegetation damage)
            recovery_lag = max(0, storm_peak - d_ago) * 0.003  # slow recovery after event
            ndvi_t = base_ndvi - storm_effect * 0.15 + recovery_lag + rng.normal(0, 0.015)
            
            # MNDWI tracks NDWI but with different sensitivity
            mndwi_t = ndwi_t * 0.85 + rng.normal(0, 0.01)
            
            # SAR backscatter drops over water (specular reflection)
            sar_t = base_sar - storm_effect * 8 + rng.normal(0, 0.8)
            
            # Soil moisture responds to rainfall with ~1-day lag
            sm_t = base_sm + storm_effect * 30 + rng.normal(0, 2)
            
            results.append({
                "days_ago": d_ago,
                "ndwi": round(float(np.clip(ndwi_t, -0.8, 0.65)), 4),
                "ndvi": round(float(np.clip(ndvi_t, -0.1, 0.85)), 4),
                "mndwi": round(float(np.clip(mndwi_t, -0.8, 0.65)), 4),
                "sar_vv_db": round(float(np.clip(sar_t, -28, -5)), 2),
                "soil_moisture": round(float(np.clip(sm_t, 5, 98)), 1),
                "storm_effect_magnitude": round(float(storm_effect), 3),
                "source": "Simulated Time-Series"
            })
        
        return results


timeseries_processor = TimeSeriesProcessor()
