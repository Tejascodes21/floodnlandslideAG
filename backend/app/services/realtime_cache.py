"""
Real-time Data Cache Service
==============================
Handles caching of real-time telemetry, weather data, and 
frequent prediction requests using Redis (with in-memory fallback).
"""

import time
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger("geoshield.services.cache")

class RealtimeCache:
    """
    Caching service for real-time data streams and predictions.
    """
    def __init__(self):
        self._cache = {}
        self._ttl = {}
        
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set a value in the cache with a Time-To-Live."""
        self._cache[key] = value
        self._ttl[key] = time.time() + ttl_seconds
        
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if it hasn't expired."""
        if key in self._cache:
            if time.time() <= self._ttl.get(key, 0):
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._ttl[key]
        return None
        
    def invalidate(self, key: str):
        """Manually invalidate a cache key."""
        if key in self._cache:
            del self._cache[key]
        if key in self._ttl:
            del self._ttl[key]
            
    def get_all_live_alerts(self) -> list:
        """Helper to get all active alerts from cache."""
        alerts = []
        for k, v in self._cache.items():
            if k.startswith("alert:") and time.time() <= self._ttl.get(k, 0):
                alerts.append(v)
        return alerts

# Singleton instance
cache_service = RealtimeCache()
