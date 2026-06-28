"""
Raster Export Pipeline
=======================
Handles export of processed imagery and analysis results to
GeoTIFF, PNG tiles, and JSON formats for frontend consumption.
"""

import numpy as np
import json
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("geoshield.gee.export")

EXPORT_DIR = Path(__file__).parent.parent.parent / "exports"


class RasterExporter:
    """
    Exports geospatial analysis results in multiple formats.
    """
    
    def __init__(self):
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    def export_risk_grid_json(self, grid_data: List[Dict],
                               lat: float, lon: float,
                               grid_size: int = 8,
                               filename: Optional[str] = None) -> str:
        """
        Exports a risk analysis grid to GeoJSON-like format
        for frontend heatmap rendering.
        """
        if not filename:
            filename = f"risk_grid_{lat:.2f}_{lon:.2f}.json"
        
        filepath = EXPORT_DIR / filename
        
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "center": {"lat": lat, "lon": lon},
                "grid_size": grid_size,
                "crs": "EPSG:4326"
            },
            "features": []
        }
        
        for cell in grid_data:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [cell.get("lon", lon), cell.get("lat", lat)]
                },
                "properties": {
                    k: v for k, v in cell.items() if k not in ("lat", "lon")
                }
            }
            geojson["features"].append(feature)
        
        with open(filepath, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        logger.info(f"Exported risk grid to {filepath}")
        return str(filepath)
    
    def export_timeseries_csv(self, timeseries: List[Dict],
                               lat: float, lon: float,
                               filename: Optional[str] = None) -> str:
        """Exports time-series data to CSV format."""
        if not filename:
            filename = f"timeseries_{lat:.2f}_{lon:.2f}.csv"
        
        filepath = EXPORT_DIR / filename
        
        if not timeseries:
            return str(filepath)
        
        headers = list(timeseries[0].keys())
        lines = [",".join(headers)]
        
        for row in timeseries:
            values = [str(row.get(h, "")) for h in headers]
            lines.append(",".join(values))
        
        with open(filepath, 'w') as f:
            f.write("\n".join(lines))
        
        logger.info(f"Exported time-series CSV to {filepath}")
        return str(filepath)
    
    def export_prediction_report(self, prediction_data: Dict,
                                  filename: Optional[str] = None) -> str:
        """Exports full prediction report as structured JSON."""
        lat = prediction_data.get("lat", 0)
        lon = prediction_data.get("lon", 0)
        
        if not filename:
            filename = f"prediction_report_{lat:.2f}_{lon:.2f}.json"
        
        filepath = EXPORT_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(prediction_data, f, indent=2, default=str)
        
        logger.info(f"Exported prediction report to {filepath}")
        return str(filepath)
    
    def generate_heatmap_tiles(self, grid_data: List[Dict],
                                value_key: str = "risk_score",
                                grid_size: int = 8) -> Dict:
        """
        Generates a raster-style heatmap array from grid data
        for canvas-based frontend rendering.
        
        Returns:
            Dict with normalized 2D array, bounds, and color stops
        """
        matrix = np.zeros((grid_size, grid_size))
        
        for cell in grid_data:
            r = cell.get("row", 0)
            c = cell.get("col", 0)
            if 0 <= r < grid_size and 0 <= c < grid_size:
                matrix[r, c] = cell.get(value_key, 0)
        
        # Normalize to 0-1 range
        vmin, vmax = float(np.min(matrix)), float(np.max(matrix))
        if vmax > vmin:
            normalized = ((matrix - vmin) / (vmax - vmin)).tolist()
        else:
            normalized = matrix.tolist()
        
        return {
            "matrix": normalized,
            "grid_size": grid_size,
            "value_range": {"min": round(vmin, 4), "max": round(vmax, 4)},
            "color_stops": [
                {"value": 0.0, "color": "#00ff00", "label": "Low Risk"},
                {"value": 0.25, "color": "#ffff00", "label": "Moderate"},
                {"value": 0.50, "color": "#ff8800", "label": "High"},
                {"value": 0.75, "color": "#ff0000", "label": "Extreme"},
                {"value": 1.0, "color": "#880000", "label": "Critical"}
            ]
        }


raster_exporter = RasterExporter()
