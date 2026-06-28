export interface Coordinates {
  lat: number;
  lon: number;
}

export interface WeatherTelemetry {
  temperature_c: number;
  humidity_percent: number;
  wind_speed_kmh: number;
  wind_direction_deg: number;
  precipitation_accumulations: {
    rain_1h_mm: number;
    rain_24h_mm: number;
    rain_72h_mm: number;
  };
  forecast_summary: string;
}

export interface CnnSatelliteAnalysis {
  inundation_ratio_percentage: number;
  inundation_class: string;
  water_depth_est_m: number;
  processing_latency_ms: number;
}

export interface ShapValue {
  feature: string;
  contribution: number;
  details: string;
}

export interface ExplainabilityData {
  shap_values: ShapValue[];
  reasoning_summary: string;
}

export interface HazardAlert {
  triggered: boolean;
  severity: 'low' | 'moderate' | 'high' | 'extreme' | 'none';
  alerts: Array<{
    type: string;
    message: string;
    threshold_value: number;
    current_value: number;
  }>;
}

export interface EvacuationCamp {
  name: string;
  lat: number;
  lon: number;
}

export interface HazardPrediction {
  prediction_id: number;
  coordinates: Coordinates;
  location_name: string;
  elevation: number;
  slope: number;
  ndwi: number;
  ndvi: number;
  weather: WeatherTelemetry;
  cnn_satellite_analysis: CnnSatelliteAnalysis;
  flood_risk: {
    probability: number;
    percentage: number;
    severity: string;
  };
  landslide_risk: {
    probability: number;
    percentage: number;
    susceptibility: string;
  };
  explainability: ExplainabilityData;
  alerts: HazardAlert;
  nearest_evacuation_camp: EvacuationCamp | null;
  source_status: string;
  data_source: 'live' | 'simulation';
}

export interface Volunteer {
  id: number;
  full_name: string;
  phone: string;
  lat: number;
  lon: number;
  vehicle_type: string;
  skills: string;
  active: boolean;
}

export interface SOSAlert {
  id?: number;
  reporter_name: string;
  phone: string;
  lat: number;
  lon: number;
  emergency_type: string;
  details: string;
  voice_note_path?: string | null;
  status: 'Pending' | 'Dispatched' | 'Resolved';
  volunteer_id?: number | null;
}

export interface RescueMission {
  mission_id: number;
  volunteer_name: string;
  vehicle: string;
  citizen: string;
  emergency_type: string;
  route: Coordinates[];
  status: string;
}

export interface CommunityReport {
  id?: number;
  reporter_name: string;
  lat: number;
  lon: number;
  incident_type: string;
  details: string;
  upvotes: number;
  status?: 'Unverified' | 'Verified' | 'Resolved' | 'Spam';
  created_at?: string;
}

export interface SystemStatus {
  status: 'Green' | 'Yellow' | 'Red';
  latency_ms: number;
  services: {
    geoprocessor: string;
    xgboost_classifier: string;
    random_forest_landslide: string;
    cnn_chunker: string;
    sqlite_spatial_session: string;
  };
}

export interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
  action?: string | null;
  timestamp: Date;
}
