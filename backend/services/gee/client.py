"""
GEE Client — Authentication & Connection Management
=====================================================
Handles Google Earth Engine SDK initialization with graceful
fallback to simulation mode when credentials are unavailable.
"""

import logging
from typing import Optional

logger = logging.getLogger("geoshield.gee")

try:
    import ee
    _EE_AVAILABLE = True
except ImportError:
    _EE_AVAILABLE = False
    logger.info("Google Earth Engine SDK not installed. Simulation mode active.")


class GEEClient:
    """
    Manages GEE authentication lifecycle.
    
    Supports:
      - Service account authentication (production)
      - Application default credentials
      - Interactive notebook authentication
      - Automatic fallback to high-fidelity simulation
    """
    
    def __init__(self, project_id: Optional[str] = None, service_account_key: Optional[str] = None):
        import os
        self.project_id = project_id or os.getenv("GEE_PROJECT") or os.getenv("EE_PROJECT") or "mock-gee-project"
        self.service_account_key = service_account_key or os.getenv("GEE_SERVICE_ACCOUNT_KEY") or os.getenv("EE_SERVICE_ACCOUNT_KEY")
        self.service_account_email = os.getenv("GEE_SERVICE_ACCOUNT") or os.getenv("EE_SERVICE_ACCOUNT")
        self.initialized = False
        self.mode = "simulation"
        self._attempt_init()
    
    def _attempt_init(self):
        """Attempt GEE authentication with multiple strategies."""
        if not _EE_AVAILABLE:
            logger.info("GEE SDK unavailable — running in Fidelity Simulation Mode.")
            return
        
        strategies = [
            ("service_account", self._init_service_account),
            ("application_default", self._init_app_default),
        ]
        
        import os
        if os.getenv("GEE_INTERACTIVE_AUTH") == "true":
            strategies.append(("interactive", self._init_interactive))
        
        for name, strategy in strategies:
            try:
                strategy()
                self.initialized = True
                self.mode = "gee_live"
                logger.info(f"GEE authenticated via {name} strategy.")
                return
            except Exception as e:
                logger.debug(f"GEE auth strategy '{name}' failed: {e}")
                continue
        
        logger.warning("All GEE auth strategies failed. Using Fidelity Simulation Mode.")
    
    def _init_service_account(self):
        if not self.service_account_key:
            raise ValueError("No service account key provided")
        
        import os
        import json
        import tempfile
        
        # If the key is a path to a file, use it directly
        if os.path.exists(self.service_account_key):
            credentials = ee.ServiceAccountCredentials(self.service_account_email, key_file=self.service_account_key)
        else:
            # Check if it is inline JSON key data
            try:
                key_dict = json.loads(self.service_account_key)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(key_dict, f)
                    temp_key_path = f.name
                credentials = ee.ServiceAccountCredentials(self.service_account_email, key_file=temp_key_path)
            except Exception as e:
                raise ValueError(f"GEE_SERVICE_ACCOUNT_KEY is neither a valid file path nor valid JSON data: {e}")
        
        ee.Initialize(credentials, project=self.project_id)
    
    def _init_app_default(self):
        if self.project_id and self.project_id != "mock-gee-project":
            ee.Initialize(project=self.project_id)
        else:
            ee.Initialize()
    
    def _init_interactive(self):
        ee.Authenticate()
        if self.project_id and self.project_id != "mock-gee-project":
            ee.Initialize(project=self.project_id)
        else:
            ee.Initialize()
    
    @property
    def is_live(self) -> bool:
        return self.initialized and self.mode == "gee_live"
    
    def get_ee(self):
        """Returns the ee module if initialized, else None."""
        if self.is_live:
            return ee
        return None
    
    def status(self) -> dict:
        return {
            "gee_sdk_installed": _EE_AVAILABLE,
            "authenticated": self.initialized,
            "mode": self.mode,
            "project_id": self.project_id
        }


# Module-level singleton
gee_client = GEEClient()
