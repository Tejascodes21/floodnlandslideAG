import time
import numpy as np

class WeatherService:
    def __init__(self):
        pass

    def get_live_weather(self, lat: float, lon: float) -> dict:
        """
        Fetches live weather feeds or simulates them based on coordinate trends.
        Calculates cumulative precipitation over 24h, 48h, and 72h rolling windows.
        """
        seed = int(abs(lat * 50) + abs(lon * 50)) % 3000
        np.random.seed(seed)
        
        # Determine seasonal rainfall multipliers (simulates monsoons/tropical storms in lowlands)
        in_monsoon_belt = (lat > 5.0 and lat < 28.0) and (lon > 68.0 and lon < 97.0)
        base_rain_prob = 0.55 if in_monsoon_belt else 0.25
        
        is_raining = np.random.rand() < base_rain_prob
        
        # Cumulative rainfall calculations (triggers for sequential landslide and flood accumulation risks)
        if is_raining:
            rain_24h = float(np.random.gamma(shape=2.0, scale=18.0)) # typical storm rainfall (up to 100mm)
            rain_48h = rain_24h + float(np.random.gamma(shape=1.5, scale=12.0))
            rain_72h = rain_48h + float(np.random.gamma(shape=1.0, scale=8.0))
        else:
            # Emulate occasional light precipitation history
            rain_24h = float(np.random.exponential(scale=1.5) if np.random.rand() > 0.7 else 0.0)
            rain_48h = rain_24h + float(np.random.exponential(scale=2.5) if np.random.rand() > 0.6 else 0.0)
            rain_72h = rain_48h + float(np.random.exponential(scale=3.5) if np.random.rand() > 0.5 else 0.0)

        # Standard parameters
        temp_base = 28.0 - (lat / 5.0)
        temp = float(np.clip(temp_base + np.random.randn() * 3, 2.0, 42.0))
        
        # Wind speed max: high wind speed indicates severe cyclonic storm cells
        wind_speed = float(np.clip(8.0 + (rain_24h * 0.3) + np.random.exponential(scale=6.0), 1.0, 110.0))
        
        # Relative humidity: high rain guarantees saturated atmospheric humidity
        rh = float(np.clip(85.0 + np.random.rand()*10.0 if rain_24h > 5 else 55.0 + np.random.rand()*25.0, 10.0, 100.0))

        return {
            "is_storming": rain_24h > 45.0,
            "temp_c": round(temp, 1),
            "humidity_pct": round(rh, 1),
            "wind_speed_kmh": round(wind_speed, 1),
            "precipitation_accumulations": {
                "rain_24h_mm": round(rain_24h, 2),
                "rain_48h_mm": round(rain_48h, 2),
                "rain_72h_mm": round(rain_72h, 2)
            },
            "timestamp": time.time()
        }

weather_service = WeatherService()
