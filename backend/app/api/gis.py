"""
GIS & Routing API Endpoints
=============================
Provides endpoints for evacuation routes, AOI bounds, and terrain profiles.
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Dict, Optional
import math
import zlib
import struct

from app.services.evacuation import evacuation_router

router = APIRouter()

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    hazard_type: Optional[str] = "flood"

@router.post("/route")
async def get_safe_route(request: RouteRequest):
    """
    Returns a safe evacuation route avoiding hazardous areas.
    """
    try:
        route_data = evacuation_router.calculate_safe_route(
            request.start_lat, request.start_lon,
            request.end_lat, request.end_lon,
            request.hazard_type
        )
        return {"status": "success", "data": route_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_mock_satellite_tile(band: str, z: int, x: int, y: int) -> bytes:
    # 256x256 tile size
    width = 256
    height = 256
    
    # We can create a nice pseudo-spectral pattern based on tile coordinates
    # Let's generate a color palette based on the band:
    # rgb: True Color (satellite terrain)
    # ndwi: Water index (mostly dark/black with glowing neon cyan/blue water bodies)
    # ndvi: Vegetation (deep lush greens, yellow/brown sparse soil)
    # dem: Elevation (red-orange-yellow-contour gradients)
    
    # Let's write the raw pixel data
    scanline_len = width * 3 + 1
    raw_data = bytearray(scanline_len * height)
    
    # Create some variation across the tile
    freq = 0.05
    
    for px_y in range(height):
        # Scanline filter byte is 0 (None)
        raw_data[px_y * scanline_len] = 0
        
        # Calculate coordinate-based variables
        lat_val = (y * 256 + px_y) * freq
        
        for px_x in range(width):
            lon_val = (x * 256 + px_x) * freq
            
            # Combine sin/cos to make a nice organic looking wave/terrain pattern
            val1 = math.sin(lon_val * 0.1) * math.cos(lat_val * 0.1)
            val2 = math.sin(lon_val * 0.03 + 2.0) * math.sin(lat_val * 0.04)
            h = (val1 + val2 + 2.0) / 4.0 # normalized to 0..1
            
            # Add some higher frequency noise using simple hash
            # to make it look like raw satellite texture
            pixel_hash = ((px_x * 127 + px_y * 313) + (x * 17 + y * 23)) % 100
            noise = (pixel_hash - 50) / 500.0 # -0.1 to 0.1
            h = max(0.0, min(1.0, h + noise))
            
            # Color assignment based on band
            if band == 'ndwi':
                # NDWI: Mostly dark water background with cyan water bodies (h > 0.58)
                if h > 0.58:
                    r_val = 6
                    g_val = 182
                    b_val = 212
                elif h > 0.53:
                    r_val = 11
                    g_val = 40
                    b_val = 100
                else:
                    r_val = 11
                    g_val = 16
                    b_val = 29
            elif band == 'ndvi':
                # NDVI: Lush greens (h > 0.45), barren brown (h < 0.25)
                if h > 0.45:
                    r_val = 5
                    g_val = 150
                    b_val = 105
                elif h > 0.25:
                    r_val = 15
                    g_val = 60
                    b_val = 30
                else:
                    r_val = 66
                    g_val = 32
                    b_val = 10
            elif band == 'dem':
                # DEM: Elevation shading from red/orange/yellow/contour down to amber
                if h > 0.7:
                    r_val = 220
                    g_val = 38
                    b_val = 38
                elif h > 0.45:
                    r_val = 249
                    g_val = 115
                    b_val = 22
                elif h > 0.25:
                    r_val = 234
                    g_val = 179
                    b_val = 8
                else:
                    r_val = 69
                    g_val = 26
                    b_val = 3
            else: # rgb (default)
                # True Color: Dark green forests, blue lakes, grey structures
                if h > 0.6:
                    r_val = 30
                    g_val = 58
                    b_val = 138
                elif h > 0.35:
                    r_val = 20
                    g_val = 80
                    b_val = 50
                elif h > 0.25:
                    r_val = 74
                    g_val = 78
                    b_val = 105
                else:
                    r_val = 15
                    g_val = 21
                    b_val = 36
            
            # Write to raw_data
            offset = px_y * scanline_len + 1 + px_x * 3
            raw_data[offset] = r_val
            raw_data[offset+1] = g_val
            raw_data[offset+2] = b_val
            
    # PNG framing
    png = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    png += struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data))
    
    compressed = zlib.compress(raw_data)
    png += struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', zlib.crc32(b'IDAT' + compressed))
    
    png += struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND'))
    return bytes(png)

@router.get("/tile/{band}/{z}/{x}/{y}")
async def get_satellite_tile(band: str, z: int, x: int, y: int):
    """
    Returns a satellite tile image (PNG) for the specified band and tile coordinates.
    """
    if band not in ["rgb", "ndwi", "ndvi", "dem"]:
        raise HTTPException(status_code=400, detail="Invalid imagery band")
    
    try:
        tile_bytes = generate_mock_satellite_tile(band, z, x, y)
        return Response(content=tile_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
