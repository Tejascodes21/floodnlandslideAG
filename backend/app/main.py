import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import ee

# Adjust path to enable clean internal packages import
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.core.config import settings
from app.db.session import init_db, SessionLocal
from app.api.auth import router as auth_router, seed_default_users
from app.api.endpoints import router as core_router
from app.api import api_router as advanced_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="GeoShield AI: Full-Stack Geospatial Disaster Intelligence & Risk Assessment Platform"
)

# Enable CORS for React/Vite local dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # 1. Initialize DB tables (creates local geoshield.db)
    init_db()
    
    # 1.5 Initialize Earth Engine
    try:
        if settings.GEE_PROJECT and settings.GEE_PROJECT != "mock-gee-project":
            ee.Initialize(project=settings.GEE_PROJECT)
        else:
            ee.Initialize()
        print("Earth Engine initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize Earth Engine: {e}")
        print("Please ensure you have run 'earthengine authenticate'")
    
    # 2. Seed default users
    db = SessionLocal()
    try:
        seed_default_users(db)
    finally:
        db.close()

# Include routers under /api prefix
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(core_router, prefix=settings.API_PREFIX)
app.include_router(advanced_router, prefix=settings.API_PREFIX)

@app.get("/")
def read_root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "Online",
        "api_docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
