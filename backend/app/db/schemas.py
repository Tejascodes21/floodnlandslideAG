from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
from app.core.config import settings

try:
    from geoalchemy2 import Geometry
    # Only use GeoAlchemy2 if PostgreSQL/PostGIS is the active database
    HAS_GEOALCHEMY = settings.DATABASE_URL.startswith("postgresql")
except ImportError:
    HAS_GEOALCHEMY = False

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(50), default="Citizen", nullable=False)  # Citizen, Volunteer, Researcher, NGO, Government, Admin
    language = Column(String(10), default="en", nullable=False)  # en, hi, mr
    emergency_contact = Column(String(100), nullable=True)
    saved_alerts_json = Column(Text, default="[]")  # Saved search locations
    registered_at = Column(DateTime, default=datetime.utcnow)

class PredictionRecord(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(200), index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    flood_prob = Column(Float, nullable=False)
    flood_severity = Column(String(50), nullable=False)
    landslide_prob = Column(Float, nullable=False)
    slope = Column(Float, nullable=False)
    ndwi = Column(Float, nullable=False)
    ndvi = Column(Float, nullable=False)
    rainfall_24h = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    shap_values_json = Column(Text, nullable=True)  # SHAP explanation payload
    created_at = Column(DateTime, default=datetime.utcnow)
    
    if HAS_GEOALCHEMY:
        geom = Column(Geometry('POINT', srid=4326), nullable=True)

class Volunteer(Base):
    __tablename__ = "volunteers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    full_name = Column(String(200), nullable=False)
    skills = Column(String(500), nullable=False)  # Medical, Rescue, Boat Operator, Food/Water
    phone = Column(String(50), nullable=False)
    vehicle_type = Column(String(100), nullable=True)  # Boat, 4x4 SUV, Truck, None
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    missions = relationship("RescueMission", back_populates="volunteer")

class SOSAlert(Base):
    __tablename__ = "sos_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    reporter_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    emergency_type = Column(String(100), nullable=False)  # Flood Trapped, Landslide Trapped, Medical, Missing, relief
    details = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    voice_note_path = Column(String(500), nullable=True)
    status = Column(String(50), default="Pending", nullable=False)  # Pending, Dispatched, Resolved
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    missions = relationship("RescueMission", back_populates="sos_alert")

class RescueMission(Base):
    __tablename__ = "rescue_missions"
    
    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"), nullable=False)
    sos_id = Column(Integer, ForeignKey("sos_alerts.id"), nullable=False)
    route_geojson = Column(Text, nullable=False)  # Safe routing coordinates
    status = Column(String(50), default="Assigned", nullable=False)  # Assigned, In Transit, Active, Completed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    volunteer = relationship("Volunteer", back_populates="missions")
    sos_alert = relationship("SOSAlert", back_populates="missions")

class CommunityReport(Base):
    __tablename__ = "community_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    reporter_name = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    incident_type = Column(String(100), nullable=False)  # Water Level Rise, Road Blockage, Mudslide, Other
    details = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    status = Column(String(50), default="Unverified", nullable=False)
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class FloodEvent(Base):
    __tablename__ = "flood_events"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    event_date = Column(DateTime, nullable=False)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    flood_severity = Column(String(50), nullable=True)
    
    if HAS_GEOALCHEMY:
        geom = Column(Geometry('POINT', srid=4326), nullable=True)

class LandslideEvent(Base):
    __tablename__ = "landslide_events"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    event_date = Column(DateTime, nullable=False)
    trigger_type = Column(String(100), nullable=True)
    landslide_size = Column(String(50), nullable=True)
    damage_level = Column(String(50), nullable=True)
    
    if HAS_GEOALCHEMY:
        geom = Column(Geometry('POINT', srid=4326), nullable=True)

class WeatherHistory(Base):
    __tablename__ = "weather_history"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    rain_24h = Column(Float, default=0.0)
    rain_72h = Column(Float, default=0.0)
    rain_7d = Column(Float, default=0.0)
    rain_30d = Column(Float, default=0.0)
    spi = Column(Float, default=0.0)
    api = Column(Float, default=0.0)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)

class TerrainFeatures(Base):
    __tablename__ = "terrain_features"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=False)
    slope = Column(Float, nullable=False)
    aspect = Column(Float, nullable=False)
    curvature = Column(Float, nullable=False)
    roughness = Column(Float, nullable=False)
    twi = Column(Float, nullable=False)
    flow_accumulation = Column(Float, nullable=False)
    drainage_density = Column(Float, nullable=False)
    river_distance = Column(Float, nullable=False)
    
    if HAS_GEOALCHEMY:
        geom = Column(Geometry('POINT', srid=4326), nullable=True)

class SatelliteFeatures(Base):
    __tablename__ = "satellite_features"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    ndvi = Column(Float, nullable=True)
    ndwi = Column(Float, nullable=True)
    mndwi = Column(Float, nullable=True)
    evi = Column(Float, nullable=True)
    savi = Column(Float, nullable=True)
    ndbi = Column(Float, nullable=True)
    sar_vv = Column(Float, nullable=True)
    sar_vh = Column(Float, nullable=True)
    
    if HAS_GEOALCHEMY:
        geom = Column(Geometry('POINT', srid=4326), nullable=True)
