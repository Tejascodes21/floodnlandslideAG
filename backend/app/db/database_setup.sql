-- =========================================================================
-- GeoShield AI — PostgreSQL + PostGIS Schema Setup Script
-- =========================================================================
-- Run this script on your PostgreSQL database cluster to enable PostGIS
-- and initialize the tables with spatial indexing.

-- 1. Enable Spatial Extensions
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Drop existing tables if they exist (to avoid conflicts)
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS satellite_features CASCADE;
DROP TABLE IF EXISTS terrain_features CASCADE;
DROP TABLE IF EXISTS weather_history CASCADE;
DROP TABLE IF EXISTS landslide_events CASCADE;
DROP TABLE IF EXISTS flood_events CASCADE;

-- 3. Create Historical Flood Events Table
CREATE TABLE flood_events (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    event_date TIMESTAMP NOT NULL,
    district VARCHAR(100),
    state VARCHAR(100),
    flood_severity VARCHAR(50),
    geom GEOMETRY(Point, 4326)
);

-- Create spatial index for flood events
CREATE INDEX idx_flood_events_geom ON flood_events USING gist(geom);
CREATE INDEX idx_flood_events_coords ON flood_events(latitude, longitude);

-- 4. Create Historical Landslide Events Table
CREATE TABLE landslide_events (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    event_date TIMESTAMP NOT NULL,
    trigger_type VARCHAR(100),
    landslide_size VARCHAR(50),
    damage_level VARCHAR(50),
    geom GEOMETRY(Point, 4326)
);

-- Create spatial index for landslide events
CREATE INDEX idx_landslide_events_geom ON landslide_events USING gist(geom);
CREATE INDEX idx_landslide_events_coords ON landslide_events(latitude, longitude);

-- 5. Create Weather History Table (IMD and OpenWeather data)
CREATE TABLE weather_history (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    date TIMESTAMP NOT NULL,
    rain_24h DOUBLE PRECISION DEFAULT 0.0,
    rain_72h DOUBLE PRECISION DEFAULT 0.0,
    rain_7d DOUBLE PRECISION DEFAULT 0.0,
    rain_30d DOUBLE PRECISION DEFAULT 0.0,
    spi DOUBLE PRECISION DEFAULT 0.0,
    api DOUBLE PRECISION DEFAULT 0.0,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION
);

CREATE INDEX idx_weather_history_coords_date ON weather_history(latitude, longitude, date);

-- 6. Create Terrain Features Table (SRTM DEM products)
CREATE TABLE terrain_features (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation DOUBLE PRECISION NOT NULL,
    slope DOUBLE PRECISION NOT NULL,
    aspect DOUBLE PRECISION NOT NULL,
    curvature DOUBLE PRECISION NOT NULL,
    roughness DOUBLE PRECISION NOT NULL,
    twi DOUBLE PRECISION NOT NULL,
    flow_accumulation DOUBLE PRECISION NOT NULL,
    drainage_density DOUBLE PRECISION NOT NULL,
    river_distance DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326)
);

CREATE INDEX idx_terrain_features_geom ON terrain_features USING gist(geom);
CREATE INDEX idx_terrain_features_coords ON terrain_features(latitude, longitude);

-- 7. Create Satellite Features Table (Sentinel Sentinel-1 & Sentinel-2 indices)
CREATE TABLE satellite_features (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    date TIMESTAMP NOT NULL,
    ndvi DOUBLE PRECISION,
    ndwi DOUBLE PRECISION,
    mndwi DOUBLE PRECISION,
    evi DOUBLE PRECISION,
    savi DOUBLE PRECISION,
    ndbi DOUBLE PRECISION,
    sar_vv DOUBLE PRECISION,
    sar_vh DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326)
);

CREATE INDEX idx_satellite_features_geom ON satellite_features USING gist(geom);
CREATE INDEX idx_satellite_features_coords_date ON satellite_features(latitude, longitude, date);

-- 8. Create Live/Interactive Predictions Record Table
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(200),
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    flood_prob DOUBLE PRECISION NOT NULL,
    flood_severity VARCHAR(50) NOT NULL,
    landslide_prob DOUBLE PRECISION NOT NULL,
    slope DOUBLE PRECISION NOT NULL,
    ndwi DOUBLE PRECISION NOT NULL,
    ndvi DOUBLE PRECISION NOT NULL,
    rainfall_24h DOUBLE PRECISION NOT NULL,
    soil_moisture DOUBLE PRECISION NOT NULL,
    shap_values_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(Point, 4326)
);

CREATE INDEX idx_predictions_geom ON predictions USING gist(geom);
CREATE INDEX idx_predictions_coords ON predictions(lat, lon);
