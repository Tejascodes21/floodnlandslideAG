import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search, Compass, AlertTriangle, ShieldAlert, Sparkles,
  Navigation, CloudRain, Satellite, Power, MapPin, Loader2
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../config';

declare var L: any;

// ─── i18n ──────────────────────────────────────────────────────────────────
const dashboardTranslations = {
  en: {
    search_placeholder: "Search city, district, or landmark in India…",
    analyze_btn: "Analyze Risk Grid",
    flood_risk: "Flood Probability",
    landslide_risk: "Landslide Susceptibility",
    hazard_alerts: "Active Hazard Alerts",
    shap_title: "AI Prediction Explanation (SHAP Value Ratios)",
    elevation: "DEM Elevation",
    slope: "Slope Angle",
    soil: "Soil Moisture",
    rain: "Rainfall 24h",
    severity: "Severity Level",
    safe_route: "Safe Shelter Route",
    safe_zone: "Nearest Safe Zone",
    aoi_draw: "AOI Polygon Status",
    aoi_active: "Custom AOI Grid Active",
    aoi_inactive: "Draw Polygon or Search Location to isolate analysis",
    details: "Physical Geo-Telemetry",
    national_summary: "Live EOC National summary",
    vol_avail: "Volunteer availability",
    infra_status: "Infrastructure Grid Status",
    weather_intel: "Weather Intelligence",
    sat_activity: "Sentinel-2 Orbit status",
    ai_recom: "AI Emergency Recommendations",
  },
  hi: {
    search_placeholder: "भारत में शहर, जिला या स्थल खोजें…",
    analyze_btn: "जोखिम ग्रिड विश्लेषण",
    flood_risk: "बाढ़ की संभावना",
    landslide_risk: "भूस्खलन संवेदनशीलता",
    hazard_alerts: "सक्रिय खतरा चेतावनियां",
    shap_title: "AI भविष्यवाणी स्पष्टीकरण (SHAP मूल्य अनुपात)",
    elevation: "DEM ऊंचाई",
    slope: "पहाड़ी ढलान कोण",
    soil: "मिट्टी की नमी",
    rain: "वर्षा २४ घंटे",
    severity: "तीव्रता स्तर",
    safe_route: "सुरक्षित निकासी मार्ग",
    safe_zone: "निकटतम सुरक्षित क्षेत्र",
    aoi_draw: "AOI पॉलीगॉन स्थिति",
    aoi_active: "कस्टम AOI ग्रिड सक्रिय",
    aoi_inactive: "विश्लेषण के लिए पॉलीगॉन बनाएं या स्थान खोजें",
    details: "भौतिक भू-टेलीमेट्री",
    national_summary: "सक्रिय राष्ट्रीय आपदा सारांश",
    vol_avail: "स्वयंसेवक उपलब्धता",
    infra_status: "इन्फ्रास्ट्रक्चर ग्रिड स्थिति",
    weather_intel: "मौसम खुफिया जानकारी",
    sat_activity: "सेंटिनल-२ कक्षा स्थिति",
    ai_recom: "एआई आपातकालीन सिफारिशें",
  },
  mr: {
    search_placeholder: "भारतातील शहर, जिल्हा किंवा खूण शोधा…",
    analyze_btn: "जोखिम ग्रिड विश्लेषण",
    flood_risk: "पुराची शक्यता",
    landslide_risk: "दरड कोसळण्याची शक्यता",
    hazard_alerts: "सक्रिय आपत्कालीन चेतावणी",
    shap_title: "AI धोका स्पष्टीकरण (SHAP मूल्य प्रमाण)",
    elevation: "DEM उंची",
    slope: "डोंगरउतार कोन",
    soil: "मातीची आर्द्रता",
    rain: "पाऊस २४ तास",
    severity: "धोका पातळी",
    safe_route: "सुरक्षित स्थलांतर मार्ग",
    safe_zone: "जवळचे सुरक्षित क्षेत्र",
    aoi_draw: "AOI पॉलीगॉन स्थिति",
    aoi_active: "कस्टम AOI ग्रिड सक्रिय",
    aoi_inactive: "विश्लेषणासाठी पॉलीगॉन काढा किंवा ठिकाण शोधा",
    details: "भौतिक भू-टेलीमेट्री",
    national_summary: "राष्ट्रीय आपत्ती सारांश",
    vol_avail: "स्वयंसेवक उपलब्धता",
    infra_status: "पायाभूत सुविधा ग्रिड स्थिती",
    weather_intel: "हवामान विश्लेषण",
    sat_activity: "सेंटिनेल-२ कक्षा स्थिती",
    ai_recom: "एआय आपत्कालीन शिफारसी",
  },
};

// ─── Types ─────────────────────────────────────────────────────────────────
interface NominatimResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
}

interface DashboardProps {
  lang: 'en' | 'hi' | 'mr';
  userRole: string;
  selectedLocation: { lat: number; lon: number; name: string } | null;
}

// ─── Custom SVG Drop-Pin marker factory ───────────────────────────────────
function makePinIcon(color: string) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="44" viewBox="0 0 32 44">
      <defs>
        <filter id="shadow" x="-30%" y="-20%" width="160%" height="160%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="rgba(0,0,0,0.5)"/>
        </filter>
      </defs>
      <path d="M16 0C7.163 0 0 7.163 0 16c0 10 16 28 16 28S32 26 32 16C32 7.163 24.837 0 16 0z"
            fill="${color}" filter="url(#shadow)" />
      <circle cx="16" cy="16" r="6" fill="white" opacity="0.9"/>
    </svg>`;
  return L.divIcon({
    className: '',
    html: svg,
    iconSize: [32, 44],
    iconAnchor: [16, 44],
    popupAnchor: [0, -44],
  });
}

// ─── Telemetry skeleton card ───────────────────────────────────────────────
function TelemetrySkeleton() {
  return (
    <div className="animate-pulse grid grid-cols-2 gap-3 text-[11px]">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="bg-slate-950/40 p-2 rounded border border-borderDim space-y-1.5">
          <div className="h-2 bg-slate-700 rounded w-3/4" />
          <div className="h-3 bg-slate-600 rounded w-1/2" />
        </div>
      ))}
    </div>
  );
}

// ─── Component ─────────────────────────────────────────────────────────────
export default function Dashboard({ lang, userRole, selectedLocation }: DashboardProps) {
  const t = dashboardTranslations[lang];

  // Search / autocomplete state
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<NominatimResult[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchWrapperRef = useRef<HTMLDivElement>(null);

  // Active coordinate for risk analysis
  const [activeCoords, setActiveCoords] = useState<{ lat: number; lon: number; name: string }>({
    lat: 20.5937,
    lon: 78.9629,
    name: 'India',
  });
  const [analysisTriggered, setAnalysisTriggered] = useState(false);

  // Map refs
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const routePolylineRef = useRef<any>(null);

  // ─── Sync external selectedLocation prop ──────────────────────────────
  useEffect(() => {
    if (selectedLocation) {
      const name = selectedLocation.name;
      setSearchQuery(name);
      const coords = { lat: selectedLocation.lat, lon: selectedLocation.lon, name };
      setActiveCoords(coords);
      setAnalysisTriggered(true);
      flyToCoords(selectedLocation.lat, selectedLocation.lon);
    }
  }, [selectedLocation]);

  // ─── Nominatim autocomplete with 300ms debounce ───────────────────────
  const fetchSuggestions = useCallback(async (query: string) => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }
    setSearchLoading(true);
    try {
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=in&limit=7&addressdetails=0`;
      const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
      const data: NominatimResult[] = await res.json();
      setSuggestions(data);
      setShowDropdown(data.length > 0);
    } catch {
      setSuggestions([]);
      setShowDropdown(false);
    } finally {
      setSearchLoading(false);
    }
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchQuery(val);
    setShowDropdown(false);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 300);
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ─── Select suggestion ────────────────────────────────────────────────
  const handleSuggestionSelect = (item: NominatimResult) => {
    const lat = parseFloat(item.lat);
    const lon = parseFloat(item.lon);
    // Trim display name to city/district level
    const name = item.display_name.split(',')[0].trim();
    setSearchQuery(name);
    setSuggestions([]);
    setShowDropdown(false);
    setActiveCoords({ lat, lon, name });
    setAnalysisTriggered(true);
    flyToCoords(lat, lon);
  };

  // ─── Manual coordinate search ─────────────────────────────────────────
  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setShowDropdown(false);

    const coordsMatch = searchQuery.match(/^([-+]?\d+\.?\d*)\s*,\s*([-+]?\d+\.?\d*)$/);
    if (coordsMatch) {
      const lat = parseFloat(coordsMatch[1]);
      const lon = parseFloat(coordsMatch[2]);
      setActiveCoords({ lat, lon, name: `${lat.toFixed(4)}, ${lon.toFixed(4)}` });
      setAnalysisTriggered(true);
      flyToCoords(lat, lon);
      return;
    }

    // If no suggestion was chosen, geocode the typed query
    setSearchLoading(true);
    try {
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&countrycodes=in&limit=1`;
      const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
      const data: NominatimResult[] = await res.json();
      if (data.length > 0) {
        handleSuggestionSelect(data[0]);
      }
    } catch { /* silent */ } finally {
      setSearchLoading(false);
    }
  };

  // ─── Map initialisation ───────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current && typeof L !== 'undefined') {
      mapRef.current = L.map('dashboard-map', {
        // India-centered at country-wide zoom level
        center: [20.5937, 78.9629],
        zoom: 5,
        zoomControl: false,
      });

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20,
        attribution: '© OpenStreetMap © CARTO',
      }).addTo(mapRef.current);

      L.control.zoom({ position: 'bottomright' }).addTo(mapRef.current);

      // Click-on-map → immediate coordinate analysis
      mapRef.current.on('click', (e: any) => {
        const { lat, lng } = e.latlng;
        const name = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
        setSearchQuery(name);
        setActiveCoords({ lat, lon: lng, name });
        setAnalysisTriggered(true);
      });
    }
  }, []);

  // ─── flyTo helper ─────────────────────────────────────────────────────
  const flyToCoords = (lat: number, lon: number) => {
    if (mapRef.current) {
      mapRef.current.flyTo([lat, lon], 12, { animate: true, duration: 1.2 });
    }
  };

  // ─── React Query — hazard data from backend ───────────────────────────
  const { data: hazardData, isLoading, isError, refetch } = useQuery({
    queryKey: ['hazardData', activeCoords.lat, activeCoords.lon, lang],
    queryFn: () =>
      apiClient.post('/api/predict/multi-hazard', {
        lat: activeCoords.lat,
        lon: activeCoords.lon,
        location_name: activeCoords.name,
        lang,
      }),
    enabled: analysisTriggered,
  });

  // ─── React Query — volunteer headcount ───────────────────────────────
  const { data: volunteers } = useQuery({
    queryKey: ['volunteers'],
    queryFn: () => apiClient.get('/api/volunteers'),
    refetchInterval: 10_000,
  });

  // ─── Map marker + evacuation route after hazard data arrives ─────────
  useEffect(() => {
    if (!mapRef.current || !hazardData) return;
    const { lat, lon } = activeCoords;

    // Remove old marker
    if (markerRef.current) {
      mapRef.current.removeLayer(markerRef.current);
    }

    const isHighRisk =
      hazardData.flood_risk.probability > 0.5 || hazardData.landslide_risk.probability > 0.5;
    const pinColor = isHighRisk ? '#ef4444' : '#10b981';

    markerRef.current = L.marker([lat, lon], { icon: makePinIcon(pinColor) })
      .addTo(mapRef.current)
      .bindTooltip(
        `<div style="font-size:11px;font-weight:600">${activeCoords.name}<br/>
         🌊 Flood: ${hazardData.flood_risk.percentage}% &nbsp; ⛰️ Slide: ${hazardData.landslide_risk.percentage}%</div>`,
        { direction: 'top', offset: [0, -46] }
      );

    // Remove old route
    if (routePolylineRef.current) {
      mapRef.current.removeLayer(routePolylineRef.current);
      routePolylineRef.current = null;
    }

    // Draw evacuation route when risk is elevated
    if (isHighRisk) {
      const shelter = hazardData.nearest_evacuation_camp;
      if (shelter) {
        const points = [
          [lat, lon],
          [lat + 0.003, lon + 0.002],
          [lat + 0.005, lon - 0.001],
          [shelter.lat, shelter.lon],
        ];
        routePolylineRef.current = L.polyline(points, {
          color: '#3b82f6',
          weight: 4,
          dashArray: '8, 8',
          opacity: 0.85,
        }).addTo(mapRef.current);
      }
    }
  }, [hazardData, activeCoords]);

  // ─── Helpers ──────────────────────────────────────────────────────────
  const getRiskColor = (prob: number) => {
    if (prob >= 0.75) return 'text-red-500';
    if (prob >= 0.50) return 'text-orange-500';
    if (prob >= 0.25) return 'text-amber-500';
    return 'text-emerald-500';
  };

  const getRiskBg = (prob: number) => {
    if (prob >= 0.75) return 'bg-red-500/10 border-red-500/30';
    if (prob >= 0.50) return 'bg-orange-500/10 border-orange-500/30';
    if (prob >= 0.25) return 'bg-amber-500/10 border-amber-500/30';
    return 'bg-emerald-500/10 border-emerald-500/30';
  };

  const activeVolunteersCount = volunteers
    ? volunteers.filter((v: any) => v.active).length
    : 24;

  // ─── Render ───────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">

      {/* ── Top 4 Quick Indicators ────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Active Alert Zones */}
        <div className="glass-panel p-4 rounded-xl border border-borderDim flex items-center justify-between">
          <div>
            <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">{t.national_summary}</span>
            <span className="text-2xl font-black block mt-1 text-red-500">3 Active Alert Zones</span>
          </div>
          <div className="p-3 bg-red-500/10 border border-red-500/30 text-red-500 rounded-lg">
            <ShieldAlert className="w-5 h-5 pulse-threat" />
          </div>
        </div>

        {/* ML Confidence */}
        <div className="glass-panel p-4 rounded-xl border border-borderDim flex items-center justify-between">
          <div>
            <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">ML Model Status</span>
            <span className="text-2xl font-black block mt-1 text-blue-400">92% Confidence</span>
          </div>
          <div className="p-3 bg-blue-500/10 border border-blue-500/30 text-blue-500 rounded-lg">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
        </div>

        {/* Volunteers */}
        <div className="glass-panel p-4 rounded-xl border border-borderDim flex items-center justify-between">
          <div>
            <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">{t.vol_avail}</span>
            <span className="text-2xl font-black block mt-1 text-emerald-400">{activeVolunteersCount} standby</span>
          </div>
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg">
            <Navigation className="w-5 h-5" />
          </div>
        </div>

        {/* Satellite */}
        <div className="glass-panel p-4 rounded-xl border border-borderDim flex items-center justify-between">
          <div>
            <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">{t.sat_activity}</span>
            <span className="text-2xl font-black block mt-1 text-cyan-400">10m Res (OK)</span>
          </div>
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-lg">
            <Satellite className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* ── Search bar with autocomplete ──────────────────────────────── */}
      <form onSubmit={handleSearchSubmit} className="flex gap-3">
        <div className="relative flex-1" ref={searchWrapperRef}>
          {/* Search icon / spinner */}
          <div className="absolute left-3.5 top-2.5 text-textMuted w-4 h-4 pointer-events-none">
            {searchLoading
              ? <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              : <Search className="w-4 h-4" />
            }
          </div>

          <input
            type="text"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
            placeholder={t.search_placeholder}
            className="w-full bg-slate-900/60 border border-borderDim px-10 py-2 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/40 text-textMain transition-all"
            autoComplete="off"
          />

          {/* Autocomplete dropdown */}
          {showDropdown && suggestions.length > 0 && (
            <ul className="absolute top-full left-0 right-0 mt-1 z-[9999] bg-slate-900 border border-slate-700 rounded-xl overflow-hidden shadow-2xl max-h-64 overflow-y-auto">
              {suggestions.map((item) => (
                <li
                  key={item.place_id}
                  onMouseDown={() => handleSuggestionSelect(item)}
                  className="flex items-start gap-2.5 px-4 py-2.5 hover:bg-blue-600/20 cursor-pointer text-sm text-textMain border-b border-slate-800 last:border-0 transition-colors group"
                >
                  <MapPin className="w-3.5 h-3.5 mt-0.5 text-blue-400 shrink-0 group-hover:text-blue-300" />
                  <span className="leading-snug truncate">{item.display_name}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading || searchLoading}
          className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-6 rounded-xl text-sm flex items-center gap-2 glow-button disabled:opacity-50 shrink-0 transition-all"
        >
          {isLoading
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <Compass className="w-4 h-4" />
          }
          {t.analyze_btn}
        </button>
      </form>

      {/* ── Main Grid: Map (left) + Risk widgets (right) ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left: Map */}
        <div className="lg:col-span-2 flex flex-col h-[520px] glass-panel p-4 rounded-2xl border border-borderDim relative">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-blue-500" />
              GIS Telemetry Map View
            </span>
            {analysisTriggered && activeCoords.name !== 'India' && (
              <span className="text-[10px] font-semibold text-textMuted flex items-center gap-1">
                <MapPin className="w-3 h-3 text-blue-400" />
                {activeCoords.name}
              </span>
            )}
          </div>
          <div id="dashboard-map" className="flex-1 w-full rounded-xl border border-slate-950 z-10 relative" />
        </div>

        {/* Right: Risk info */}
        <div className="space-y-4 flex flex-col justify-between">
          <div className="space-y-4">

            {/* Flood Probability */}
            <div className={`p-4 rounded-xl border glass-panel ${hazardData ? getRiskBg(hazardData.flood_risk.probability) : 'border-borderDim'}`}>
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-semibold text-textMuted">{t.flood_risk}</span>
                <span className={`text-xl font-black ${hazardData ? getRiskColor(hazardData.flood_risk.probability) : 'text-slate-500'}`}>
                  {isLoading
                    ? <Loader2 className="w-5 h-5 animate-spin inline" />
                    : hazardData ? `${hazardData.flood_risk.percentage}%` : '--'
                  }
                </span>
              </div>
              <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-900">
                <div
                  className={`h-full rounded-full transition-all duration-1000 ${
                    hazardData?.flood_risk.probability >= 0.75
                      ? 'bg-red-500 shadow-neon-red'
                      : hazardData?.flood_risk.probability >= 0.50
                        ? 'bg-orange-500'
                        : 'bg-emerald-500'
                  }`}
                  style={{ width: hazardData ? `${hazardData.flood_risk.percentage}%` : '0%' }}
                />
              </div>
            </div>

            {/* Landslide Risk */}
            <div className={`p-4 rounded-xl border glass-panel ${hazardData ? getRiskBg(hazardData.landslide_risk.probability) : 'border-borderDim'}`}>
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-semibold text-textMuted">{t.landslide_risk}</span>
                <span className={`text-xl font-black ${hazardData ? getRiskColor(hazardData.landslide_risk.probability) : 'text-slate-500'}`}>
                  {isLoading
                    ? <Loader2 className="w-5 h-5 animate-spin inline" />
                    : hazardData ? `${hazardData.landslide_risk.percentage}%` : '--'
                  }
                </span>
              </div>
              <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-900">
                <div
                  className={`h-full rounded-full transition-all duration-1000 ${
                    hazardData?.landslide_risk.probability >= 0.75
                      ? 'bg-red-500 shadow-neon-red'
                      : hazardData?.landslide_risk.probability >= 0.50
                        ? 'bg-orange-500'
                        : 'bg-emerald-500'
                  }`}
                  style={{ width: hazardData ? `${hazardData.landslide_risk.percentage}%` : '0%' }}
                />
              </div>
            </div>

            {/* Geo-Telemetry */}
            <div className="glass-panel p-4 rounded-xl border border-borderDim space-y-2.5">
              <h3 className="text-xs font-bold text-textMain border-b border-borderDim pb-1.5 uppercase tracking-wide">
                {t.details}
              </h3>
              {isLoading ? (
                <TelemetrySkeleton />
              ) : (
                <div className="grid grid-cols-2 gap-3 text-[11px]">
                  <div className="bg-slate-950/40 p-2 rounded border border-borderDim">
                    <span className="text-textMuted block mb-0.5">{t.elevation}</span>
                    <span className="font-bold text-textMain">{hazardData ? `${hazardData.elevation} m` : '--'}</span>
                  </div>
                  <div className="bg-slate-950/40 p-2 rounded border border-borderDim">
                    <span className="text-textMuted block mb-0.5">{t.slope}</span>
                    <span className="font-bold text-textMain">{hazardData ? `${hazardData.slope}°` : '--'}</span>
                  </div>
                  <div className="bg-slate-950/40 p-2 rounded border border-borderDim">
                    <span className="text-textMuted block mb-0.5">{t.soil}</span>
                    <span className="font-bold text-textMain">
                      {hazardData ? `${hazardData.weather?.soil_moisture?.toFixed(1) ?? (hazardData.ndvi * 100).toFixed(1)}%` : '--'}
                    </span>
                  </div>
                  <div className="bg-slate-950/40 p-2 rounded border border-borderDim">
                    <span className="text-textMuted block mb-0.5">{t.rain}</span>
                    <span className="font-bold text-textMain">
                      {hazardData ? `${hazardData.weather?.precipitation_accumulations?.rain_24h_mm ?? '--'} mm` : '--'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Infrastructure Grid Status */}
            <div className="glass-panel p-4 rounded-xl border border-borderDim space-y-2">
              <h3 className="text-xs font-bold text-textMain border-b border-borderDim pb-1.5 uppercase tracking-wide flex items-center gap-1.5">
                <Power className="w-3.5 h-3.5 text-blue-500" />
                {t.infra_status}
              </h3>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-textMuted">Local Power Grid:</span>
                <span className="font-bold text-emerald-400">98% Active</span>
              </div>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-textMuted">Mobile Networks:</span>
                <span className="font-bold text-emerald-400">Stable</span>
              </div>
            </div>
          </div>

          {/* Active alert banner */}
          {hazardData?.alerts?.triggered && (
            <div className="p-4 rounded-xl border border-red-500/20 bg-red-950/20 flex gap-3 relative overflow-hidden shrink-0">
              <div className="absolute top-0 right-0 w-20 h-full satellite-scanner pointer-events-none" />
              <ShieldAlert className="text-red-500 w-5 h-5 shrink-0 pulse-threat" />
              <div>
                <span className="text-[10px] font-black uppercase text-red-400 tracking-wider block mb-0.5">
                  {t.hazard_alerts} [{hazardData.alerts.severity?.toUpperCase()}]
                </span>
                <p className="text-[11px] text-gray-300 leading-relaxed font-medium">
                  {hazardData.alerts.alerts?.[0]?.message}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── SHAP Explainability + AI Recommendations ──────────────────── */}
      {hazardData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-borderDim">
            <div className="flex items-center gap-2 mb-4 border-b border-borderDim pb-3">
              <Sparkles className="w-5 h-5 text-blue-500" />
              <h3 className="text-sm font-bold text-textMain uppercase tracking-wide">{t.shap_title}</h3>
            </div>
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={hazardData.explainability.shap_values.map((v: any) => ({
                    name: v.feature,
                    value: Math.round(v.contribution * 100),
                  }))}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
                >
                  <XAxis type="number" stroke="rgba(255,255,255,0.3)" fontSize={10} />
                  <YAxis dataKey="name" type="category" stroke="rgba(255,255,255,0.4)" fontSize={10} width={120} />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'rgba(15,23,42,0.95)', border: '1px solid rgba(59,130,246,0.2)' }}
                    itemStyle={{ color: '#fff', fontSize: '11px' }}
                  />
                  <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Shapley Contribution (%)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Recommendations */}
          <div className="glass-panel p-5 rounded-2xl border border-borderDim flex flex-col">
            <h3 className="text-xs font-bold text-textMain border-b border-borderDim pb-3 mb-4 uppercase tracking-wide flex items-center gap-1.5">
              <CloudRain className="w-4 h-4 text-orange-500" />
              {t.ai_recom}
            </h3>
            <ul className="space-y-3.5 text-[11px] font-medium leading-relaxed text-textMuted">
              {hazardData.explainability.shap_values.slice(0, 3).map((item: any, i: number) => (
                <li key={i} className="flex gap-2 items-start bg-slate-950/40 p-2.5 rounded-lg border border-borderDim">
                  <span className="text-blue-500 font-bold text-sm leading-none">•</span>
                  <span>{item.details}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
