import numpy as np
import time

try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False

class EarthEngineService:
    def __init__(self):
        self.initialized = False
        if GEE_AVAILABLE:
            try:
                import os
                self.project_id = os.getenv("GEE_PROJECT") or os.getenv("EE_PROJECT") or "mock-gee-project"
                self.service_account_key = os.getenv("GEE_SERVICE_ACCOUNT_KEY") or os.getenv("EE_SERVICE_ACCOUNT_KEY")
                self.service_account_email = os.getenv("GEE_SERVICE_ACCOUNT") or os.getenv("EE_SERVICE_ACCOUNT")

                if self.service_account_key:
                    import json
                    import tempfile
                    if os.path.exists(self.service_account_key):
                        credentials = ee.ServiceAccountCredentials(self.service_account_email, key_file=self.service_account_key)
                    else:
                        try:
                            key_dict = json.loads(self.service_account_key)
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                                json.dump(key_dict, f)
                                temp_key_path = f.name
                            credentials = ee.ServiceAccountCredentials(self.service_account_email, key_file=temp_key_path)
                        except Exception as e:
                            raise ValueError(f"GEE_SERVICE_ACCOUNT_KEY is neither a valid file path nor valid JSON data: {e}")

                    ee.Initialize(credentials, project=self.project_id)
                    self.initialized = True
                    print("Google Earth Engine service authenticated and initialized using service account.")
                else:
                    try:
                        ee.Initialize(project=self.project_id)
                        self.initialized = True
                        print("Google Earth Engine service initialized using default credentials.")
                    except Exception as default_err:
                        raise default_err
                
                # Also synchronize the gee_client singleton mode
                from services.gee import gee_client
                gee_client.initialized = True
                gee_client.mode = "gee_live"
            except Exception as e:
                print(f"GEE Initialization skipped: {e}. Running in Fidelity Simulation Mode.")
        else:
            print("Google Earth Engine library not found. Running in Fidelity Simulation Mode.")

    def get_geospatial_features(self, lat: float, lon: float) -> dict:
        """
        Fetches Sentinel and DEM features for given coordinates.
        In simulation mode, calculates highly realistic, deterministic geostatistical parameters 
        based on geographical wave equations (ensuring the same coords yield consistent terrain).
        """
        if self.initialized:
            try:
                from services.gee.sentinel import sentinel_processor
                from services.gee.terrain import terrain_processor
                from services.gee.hydrology import hydrology_processor
                from services.gee.indices import index_calculator
                
                # 1. Fetch Sentinel-2 composite and calculate NDVI and NDWI
                s2_data = sentinel_processor.fetch_sentinel2_composite(lat, lon)
                bands = s2_data.get("bands", s2_data)
                spectral = index_calculator.compute_all(bands)
                ndvi = spectral.get("ndvi", 0.0)
                ndwi = spectral.get("ndwi", 0.0)
                
                # 2. Fetch Sentinel-1 SAR VV backscatter
                s1_data = sentinel_processor.fetch_sentinel1_sar(lat, lon)
                sar_backscatter = s1_data.get("vv_db", -12.0)
                
                # 3. Extract terrain features: elevation and slope
                terrain_feats = terrain_processor.extract_terrain_features(lat, lon)
                elevation = terrain_feats.get("elevation_m", 100.0)
                slope = terrain_feats.get("slope_degrees", 5.0)
                
                # 4. Extract hydrology features and calculate soil moisture
                hydro_feats = hydrology_processor.extract_hydrology_features(lat, lon)
                rainfall = hydro_feats.get("rainfall", {})
                rain_24h = rainfall.get("rain_24h_mm", 0.0)
                
                # Physical basis soil moisture calculation (similar to GEEPipeline)
                veg_component = ndvi * 35
                water_component = max(0.0, ndwi) * 25
                rain_component = min(rain_24h * 0.4, 30.0)
                slope_drain = slope * 0.3
                soil_moisture = float(np.clip(30.0 + veg_component + water_component + rain_component - slope_drain, 5.0, 98.0))
                
                return {
                    "data_source": "live",
                    "source": "Google Earth Engine SDK",
                    "elevation": round(elevation, 2),
                    "slope": round(slope, 2),
                    "ndwi": round(ndwi, 4),
                    "ndvi": round(ndvi, 4),
                    "soil_moisture": round(soil_moisture, 2),
                    "sar_backscatter": round(sar_backscatter, 2),
                    "timestamp": time.time()
                }
            except Exception as e:
                print(f"Error fetching real GEE features: {e}. Falling back to simulation mode.")
        
        # High-Fidelity Geostatistical Simulation Engine
        # Make features deterministic based on lat and lon, so the same spot always returns the same terrain!
        seed = int(abs(lat * 1000) + abs(lon * 1000)) % 10000
        np.random.seed(seed)
        
        # Sinusoidal terrain generation (simulates proximity to rivers or mountain slopes)
        h_wave = np.sin(lat * 1.5) * np.cos(lon * 1.5)
        h_noise = np.sin(lat * 12.0) * np.cos(lon * 12.0) * 0.1
        
        # 1. Elevation (DEM): ranges from 5m (coastal plains) to 1200m (rugged terrains)
        elevation = float(np.clip(300 + h_wave * 450 + h_noise * 100, 5, 2500))
        
        # 2. Slope angle: correlates heavily with high elevation shifts
        slope = float(np.clip(abs(np.cos(lat * 2.0) * np.sin(lon * 2.0) * 35) + abs(h_noise * 10), 0.5, 45.0))
        
        # 3. NDWI (Normalized Difference Water Index): values closer to 1 indicate surface water bodies
        # Simulates low-elevation basins having rivers/lakes
        ndwi_base = -0.4 + (1.0 - (elevation / 800.0)) * 0.3
        if elevation < 100:  # lowland river delta simulation
            ndwi_base += 0.25
        ndwi = float(np.clip(ndwi_base + np.sin(lat * 25.0) * np.cos(lon * 25.0) * 0.15, -0.8, 0.65))
        
        # 4. NDVI (Normalized Difference Vegetation Index): vegetation density
        # High elevations or high moisture zones get denser forests, extremely high peaks get barren rock
        ndvi_base = 0.4 + (0.5 if elevation < 600 else 0.1)
        if elevation > 1600:
            ndvi_base = 0.15  # Alpine/barren zones
        ndvi = float(np.clip(ndvi_base + np.sin(lat * 8.0) * np.sin(lon * 8.0) * 0.2, -0.1, 0.85))
        
        # 5. Soil Moisture (%): highly dependent on precipitation and vegetation
        soil_moisture = float(np.clip(35 + ndvi * 40 + ndwi * 20 + np.cos(lat * 3.0) * 5, 5.0, 95.0))
        
        # 6. Sentinel-1 SAR Backscatter (dB): radar return signal
        # Water reflects away (low backscatter, e.g. -22dB), rough terrain scatters (high, e.g. -8dB)
        if ndwi > 0.1:
            sar_backscatter = float(np.clip(-22.0 + ndwi * 3.0, -25.0, -18.0))
        else:
            sar_backscatter = float(np.clip(-12.0 + (slope / 45.0) * 4.0 + (ndvi * 2.0), -16.0, -6.0))
            
        # Derived extended features
        aspect = float(np.clip(abs(np.sin(lat * 5) * 360), 0, 360))
        mndwi = float(np.clip(ndwi * 0.85, -0.8, 0.65))
        evi = float(np.clip(ndvi * 0.8, -0.3, 0.8))
        sar_vh = float(np.clip(sar_backscatter - 6.0, -35.0, -10.0))
        roughness = float(np.clip(2.0 + (slope / 60) * 30, 0.5, 50.0))
        curvature = float(np.clip(np.sin(lat * 10) * 0.005, -0.05, 0.05))
        twi = float(np.clip(np.log(10000 / max(np.tan(np.radians(max(slope, 0.1))), 0.001)), 2, 25))
        drainage_density = float(np.clip(2.5 - (elevation / 1000), 0.1, 5.0))
        river_proximity = float(np.clip(abs(np.sin(lat * 3) * 5), 0.1, 25.0))
        flow_accumulation = float(np.clip(50 + (5.0 - drainage_density) * 200, 10, 10000))
        water_occurrence = float(np.clip(50.0 + ndwi * 50.0, 0.0, 100.0))
        historical_events = int(np.clip((1 - elevation / 1000) * 5, 0, 10))

        return {
            "data_source": "simulation",
            "source": "GEE (Simulated)",
            "elevation": round(elevation, 2),
            "slope": round(slope, 2),
            "aspect": round(aspect, 2),
            "ndwi": round(ndwi, 4),
            "ndvi": round(ndvi, 4),
            "mndwi": round(mndwi, 4),
            "evi": round(evi, 4),
            "soil_moisture": round(soil_moisture, 2),
            "sar_backscatter": round(sar_backscatter, 2),
            "sar_vh": round(sar_vh, 2),
            "terrain_roughness": round(roughness, 2),
            "curvature": round(curvature, 4),
            "twi": round(twi, 2),
            "drainage_density": round(drainage_density, 3),
            "river_proximity": round(river_proximity, 3),
            "river_distance": round(river_proximity, 3),
            "flow_accumulation": round(flow_accumulation, 1),
            "water_occurrence": round(water_occurrence, 1),
            "historical_events": historical_events,
            "timestamp": time.time()
        }

    def get_time_series_satellite(self, lat: float, lon: float, days: int = 30) -> list:
        """
        Retrieves satellite time series. Uses GEE timeseries_processor when live, else simulates.
        """
        if self.initialized:
            try:
                from services.gee.timeseries import timeseries_processor
                ts_pkg = timeseries_processor.generate_storm_impact_sequence(lat, lon)
                ts = ts_pkg.get("full_timeseries", [])
                history = []
                for entry in ts:
                    history.append({
                        "days_ago": entry.get("days_ago", 0),
                        "ndwi": round(entry.get("ndwi", 0.0), 4),
                        "ndvi": round(entry.get("ndvi", 0.0), 4),
                        "sar_backscatter": round(entry.get("sar_vv_db", -12.0), 2),
                        "soil_moisture": round(entry.get("soil_moisture", 50.0), 2)
                    })
                return history
            except Exception as e:
                print(f"Error fetching real GEE time series: {e}. Falling back to simulation mode.")

        # Simulation fallback
        features = self.get_geospatial_features(lat, lon)
        history = []
        
        # Generate 5 intervals showing progression
        for i in range(days // 6):
            t_offset = days - (i * 6)
            ndwi_shift = np.sin(i / 1.5) * 0.08
            ndvi_shift = -np.sin(i / 3.0) * 0.05
            
            history.append({
                "days_ago": t_offset,
                "ndwi": round(features["ndwi"] + ndwi_shift, 4),
                "ndvi": round(features["ndvi"] + ndvi_shift, 4),
                "sar_backscatter": round(features["sar_backscatter"] - (ndwi_shift * 5), 2),
                "soil_moisture": round(np.clip(features["soil_moisture"] + (ndwi_shift * 100), 10, 100), 2)
            })
        return history

gee_service = EarthEngineService()
