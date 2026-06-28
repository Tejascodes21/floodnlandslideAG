"""
Realtime API Endpoints
=======================
Handles WebSockets and polling for live dashboard updates,
telemetry, and alert broadcasting.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from typing import List, Dict
import asyncio
import json
import time
import math

from app.services.realtime_cache import cache_service

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state
        initial_alerts = cache_service.get_all_live_alerts()
        await websocket.send_json({"type": "init", "alerts": initial_alerts})
        
        while True:
            data = await websocket.receive_text()
            # Handle incoming client messages (e.g., ping/pong or sub-region requests)
            # await manager.broadcast(f"Client said: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/broadcast_alert")
async def broadcast_alert(alert: Dict, background_tasks: BackgroundTasks):
    """
    Internal endpoint to trigger a broadcast of a new alert to all connected clients.
    """
    # Cache the alert for 1 hour
    alert_id = alert.get("id", "unknown")
    cache_service.set(f"alert:{alert_id}", alert, ttl_seconds=3600)
    
    # Broadcast asynchronously
    background_tasks.add_task(manager.broadcast, json.dumps({"type": "alert", "data": alert}))
    
    return {"status": "broadcasted", "alert_id": alert_id}

@router.get("/status")
async def get_realtime_status():
    """Poll endpoint for clients that can't use WebSockets."""
    return {
        "active_connections": len(manager.active_connections),
        "active_alerts": len(cache_service.get_all_live_alerts())
    }


# ---------------------------------------------------------------------------
# Static sensor station catalogue (would come from an IoT registry in prod)
# ---------------------------------------------------------------------------
_RIVER_STATIONS = [
    {"id": "R-101", "name": "Mithi River Gauge Terminal A", "base_depth": 3.4, "threshold": 5.0},
    {"id": "R-102", "name": "Thane Creek Delta Sensor B", "base_depth": 4.8, "threshold": 5.5},
    {"id": "R-103", "name": "Dahisar River Basin Monitor C", "base_depth": 2.1, "threshold": 4.5},
    {"id": "R-104", "name": "Ulhas River Catchment Sector D", "base_depth": 6.7, "threshold": 6.0},
]

_SOIL_PROBES = [
    {"id": "S-501", "location": "Ghatkopar Hill Slope Sector A", "base_sat": 84, "threshold": 75},
    {"id": "S-502", "location": "Sanjay Gandhi Park Slope Sector B", "base_sat": 42, "threshold": 75},
    {"id": "S-503", "location": "Lonavala Hill Pass Sector C", "base_sat": 89, "threshold": 80},
    {"id": "S-504", "location": "Khandala Ridge Sector D", "base_sat": 56, "threshold": 80},
]


def _river_status(depth: float, threshold: float) -> str:
    if depth >= threshold:
        return "Critical"
    if depth >= threshold * 0.8:
        return "Elevated"
    return "Normal"


def _soil_status(sat: float, threshold: float) -> str:
    if sat >= threshold:
        return "Critical"
    if sat >= threshold * 0.85:
        return "High"
    return "Normal"


@router.get("/telemetry")
async def get_telemetry():
    """
    Live sensor telemetry for the Risk Monitoring dashboard.
    Generates deterministic-but-evolving readings using a sine wave seeded by
    wall-clock time so every connected client sees the same synchronized value.
    """
    now = time.time()
    cycle = (now % 3600) / 3600.0  # slow hour-long diurnal cycle

    river = []
    for st in _RIVER_STATIONS:
        # +/- 0.6m oscillation around the base depth
        wave = math.sin(now / 120.0 + hash(st["id"]) % 10) * 0.6
        depth = round(max(0.5, st["base_depth"] + wave + cycle * 0.5), 2)
        river.append({
            "id": st["id"],
            "name": st["name"],
            "depth": depth,
            "threshold": st["threshold"],
            "status": _river_status(depth, st["threshold"]),
        })

    soil = []
    for p in _SOIL_PROBES:
        wave = math.sin(now / 90.0 + hash(p["id"]) % 10) * 6
        sat = round(max(5.0, min(99.0, p["base_sat"] + wave + cycle * 8)), 1)
        soil.append({
            "id": p["id"],
            "location": p["location"],
            "saturation": sat,
            "threshold": p["threshold"],
            "status": _soil_status(sat, p["threshold"]),
        })

    return {
        "timestamp": now,
        "river_stations": river,
        "soil_probes": soil,
        "network_status": "OPERATIONAL",
    }
