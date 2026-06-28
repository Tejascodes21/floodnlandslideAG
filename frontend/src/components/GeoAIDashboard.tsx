import React, { useState, useEffect, useRef } from 'react';
import { Layers, Eye, RefreshCw, Info, Maximize2, Compass, Ruler, HelpCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { API_BASE_URL, apiClient } from '../config';
import AOIDrawer from './AOIDrawer';
import FloodHeatmap from './FloodHeatmap';
import LandslideOverlay from './LandslideOverlay';

interface GeoAIDashboardProps {
  lang: 'en' | 'hi' | 'mr';
}

const translations = {
  en: {
    title: "GeoAI GIS Workstation",
    sub: "Spatial planning, multispectral overlays, and terrain analytics dashboard",
    layers: "Layer Management",
    basemaps: "Base Maps",
    vector: "Vector Overlays",
    legend: "Dynamic Legend",
    ruler: "Distance Measurement (Ruler)",
    aoi: "Isolate AOI Grid",
    fullscreen: "Toggle Fullscreen Map",
    refresh: "Redraw GIS Layers"
  },
  hi: {
    title: "जियोएआई जीआईएस वर्कस्टेशन",
    sub: "स्थानिक योजना, बहु-स्पेक्ट्रमी ओवरले और इलाके विश्लेषण डैशबोर्ड",
    layers: "परत प्रबंधन",
    basemaps: "आधार मानचित्र",
    vector: "वेक्टर ओवरले",
    legend: "गतिशील संकेत-विवरण",
    ruler: "दूरी माप (रूलर)",
    aoi: "AOI ग्रिड अलग करें",
    fullscreen: "पूर्ण स्क्रीन मैप बदलें",
    refresh: "जीआईएस परतें फिर से बनाएं"
  },
  mr: {
    title: "जिओएआय जीआयएस वर्कस्टेशन",
    sub: "स्थानिक नियोजन, बहु-स्पेक्ट्रल आच्छादन आणि भूप्रदेश विश्लेषण डॅशबोर्ड",
    layers: "थर व्यवस्थापन",
    basemaps: "बेस नकाशे",
    vector: "वेक्टर आच्छादन",
    legend: "डायनॅमिक आख्यायिका",
    ruler: "अंतर मोजमाप (पट्टी)",
    aoi: "AOI ग्रिड वेगळा करा",
    fullscreen: "पूर्ण स्क्रीन नकाशा",
    refresh: "जीआयएस स्तर पुन्हा काढा"
  }
};

export default function GeoAIDashboard({ lang }: GeoAIDashboardProps) {
  const t = translations[lang];
  const [activeBaseMap, setActiveBaseMap] = useState<'dark' | 'osm' | 'sat'>('dark');
  const [showFloodHeatmap, setShowFloodHeatmap] = useState(true);
  const [showLandslideOverlay, setShowLandslideOverlay] = useState(true);
  const [activeBand, setActiveBand] = useState<'rgb' | 'ndwi' | 'ndvi' | 'dem'>('rgb');
  const [aoiActive, setAoiActive] = useState(false);
  const [aoiBounds, setAoiBounds] = useState<any>(null);
  const [rulerActive, setRulerActive] = useState(false);
  const [measuredDistance, setMeasuredDistance] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const satelliteLayerRef = useRef<L.TileLayer | null>(null);
  const rulerPointsRef = useRef<L.LatLng[]>([]);
  const rulerPolylineRef = useRef<L.Polyline | null>(null);
  const rulerMarkersRef = useRef<any[]>([]);

  // React Query to fetch heatmap cells around Mumbai EOC center
  const { data: heatmapData } = useQuery({
    queryKey: ['heatmapData'],
    queryFn: () => {
      // Calls endpoints.py or predictions.py /api/predict/heatmap
      return apiClient.post('/api/predict/heatmap', {
        lat: 19.076,
        lon: 72.877,
        lang: lang
      }).then((res: any) => res.data);
    }
  });

  // Base tile layer URLs
  const baseMapUrls = {
    dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    osm: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    sat: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
  };

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map('gis-map-viewport', {
        center: [20.5937, 78.9629],
        zoom: 5,
        zoomControl: false
      });

      // Zoom Control
      L.control.zoom({ position: 'bottomright' }).addTo(mapRef.current);

      // Base layer
      tileLayerRef.current = L.tileLayer(baseMapUrls.dark, {
        maxZoom: 20
      }).addTo(mapRef.current);
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Sync Base Maps
  useEffect(() => {
    if (mapRef.current && tileLayerRef.current) {
      tileLayerRef.current.setUrl(baseMapUrls[activeBaseMap]);
    }
  }, [activeBaseMap]);

  // Sync Satellite Multi-spectral Band overlays
  useEffect(() => {
    if (!mapRef.current) return;

    if (satelliteLayerRef.current) {
      mapRef.current.removeLayer(satelliteLayerRef.current);
      satelliteLayerRef.current = null;
    }

    setLoading(true);
    const tileUrl = `${API_BASE_URL}/api/gis/tile/${activeBand}/{z}/{x}/{y}`;
    const satLayer = L.tileLayer(tileUrl, {
      maxZoom: 18,
      opacity: 0.55
    });

    satLayer.on('load', () => setLoading(false));
    satLayer.on('tileerror', () => setLoading(false));

    satLayer.addTo(mapRef.current);
    satelliteLayerRef.current = satLayer;
  }, [activeBand]);

  // Dynamic Ruler click handler
  useEffect(() => {
    if (!mapRef.current) return;

    const handleMapClick = (e: L.LeafletMouseEvent) => {
      if (!rulerActive) return;

      const pt = e.latlng;
      rulerPointsRef.current.push(pt);

      // Add a marker point
      const marker = L.circleMarker(pt, {
        color: '#3b82f6',
        fillColor: '#60a5fa',
        fillOpacity: 1,
        radius: 6
      }).addTo(mapRef.current!);
      rulerMarkersRef.current.push(marker);

      if (rulerPointsRef.current.length > 1) {
        const points = rulerPointsRef.current;
        
        if (rulerPolylineRef.current) {
          rulerPolylineRef.current.setLatLngs(points);
        } else {
          rulerPolylineRef.current = L.polyline(points, {
            color: '#3b82f6',
            weight: 3,
            dashArray: '5, 5'
          }).addTo(mapRef.current!);
        }

        // Calculate distance
        let totalDist = 0;
        for (let i = 0; i < points.length - 1; i++) {
          totalDist += points[i].distanceTo(points[i + 1]);
        }
        setMeasuredDistance(totalDist / 1000); // convert to km
      }
    };

    mapRef.current.on('click', handleMapClick);
    return () => {
      if (mapRef.current) {
        mapRef.current.off('click', handleMapClick);
      }
    };
  }, [rulerActive]);

  const toggleRuler = () => {
    setRulerActive(!rulerActive);
    // Clear previous ruler
    if (rulerPolylineRef.current && mapRef.current) {
      mapRef.current.removeLayer(rulerPolylineRef.current);
      rulerPolylineRef.current = null;
    }
    rulerMarkersRef.current.forEach(m => mapRef.current?.removeLayer(m));
    rulerMarkersRef.current = [];
    rulerPointsRef.current = [];
    setMeasuredDistance(null);
  };

  const handleAOIDrawn = (bounds: any) => {
    setAoiBounds(bounds);
    console.log("AOI bounding box coordinates captured", bounds);
  };

  const toggleFullscreen = () => {
    const el = document.getElementById('gis-map-viewport');
    if (el) {
      if (!document.fullscreenElement) {
        el.requestFullscreen().catch((err) => console.error(err));
      } else {
        document.exitFullscreen();
      }
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header Info Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-borderDim flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-full satellite-scanner pointer-events-none"></div>
        <div>
          <h2 className="text-lg font-bold text-textMain flex items-center gap-2">
            <Compass className="text-blue-500 w-5 h-5 shrink-0" />
            {t.title}
          </h2>
          <p className="text-xs text-textMuted mt-1">{t.sub}</p>
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={toggleFullscreen}
            className="p-2 bg-slate-900/80 hover:bg-slate-800 border border-borderDim text-textMain rounded-xl text-xs flex items-center gap-1.5 transition-all"
            title={t.fullscreen}
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          
          <button 
            onClick={toggleRuler}
            className={`p-2 border rounded-xl text-xs flex items-center gap-1.5 transition-all ${rulerActive ? 'bg-blue-600 border-blue-500 text-white' : 'bg-slate-900/80 border-borderDim text-textMain hover:bg-slate-800'}`}
          >
            <Ruler className="w-4 h-4" />
            {t.ruler}
          </button>
        </div>
      </div>

      {/* Main split dashboard grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left GIS controls side panel */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Layer Management */}
          <div className="glass-panel p-5 rounded-2xl border border-borderDim space-y-4">
            <h3 className="text-xs font-bold text-textMain border-b border-slate-900 pb-2 uppercase tracking-wide flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-500" />
              {t.layers}
            </h3>

            {/* Base maps selector */}
            <div className="space-y-1.5">
              <span className="text-[10px] text-textMuted font-bold uppercase tracking-wider block mb-1">{t.basemaps}</span>
              <div className="grid grid-cols-3 gap-1">
                {(['dark', 'osm', 'sat'] as const).map(bm => (
                  <button
                    key={bm}
                    onClick={() => setActiveBaseMap(bm)}
                    className={`py-1 rounded text-[9px] font-bold border capitalize transition-all ${activeBaseMap === bm ? 'bg-blue-600/25 border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'bg-slate-950/40 border-transparent text-slate-500 hover:text-slate-300'}`}
                  >
                    {bm}
                  </button>
                ))}
              </div>
            </div>

            {/* Satellite overlays */}
            <div className="space-y-1.5 pt-2">
              <span className="text-[10px] text-textMuted font-bold uppercase tracking-wider block mb-1">Spectral telemetry</span>
              <div className="grid grid-cols-2 gap-1 text-[9px]">
                {(['rgb', 'ndwi', 'ndvi', 'dem'] as const).map(band => (
                  <button
                    key={band}
                    onClick={() => setActiveBand(band)}
                    className={`py-1.5 rounded font-bold border uppercase transition-all ${activeBand === band ? 'bg-blue-600/25 border-blue-500/40 text-blue-300' : 'bg-slate-950/40 border-transparent text-slate-500 hover:text-slate-300'}`}
                  >
                    {band}
                  </button>
                ))}
              </div>
            </div>

            {/* Vector overlays */}
            <div className="space-y-2 pt-2">
              <span className="text-[10px] text-textMuted font-bold uppercase tracking-wider block mb-1">{t.vector}</span>
              <label className="flex items-center gap-2 text-xs font-semibold text-textMuted cursor-pointer hover:text-textMain">
                <input 
                  type="checkbox" 
                  checked={showFloodHeatmap} 
                  onChange={(e) => setShowFloodHeatmap(e.target.checked)} 
                  className="accent-blue-500"
                />
                <span>Flood hazard heatmaps</span>
              </label>

              <label className="flex items-center gap-2 text-xs font-semibold text-textMuted cursor-pointer hover:text-textMain">
                <input 
                  type="checkbox" 
                  checked={showLandslideOverlay} 
                  onChange={(e) => setShowLandslideOverlay(e.target.checked)} 
                  className="accent-orange-500"
                />
                <span>Landslide susceptibility</span>
              </label>
            </div>
            
            {/* Draw Custom AOI */}
            <button
              onClick={() => setAoiActive(!aoiActive)}
              className={`w-full py-2 rounded-xl text-xs font-bold border transition-all ${aoiActive ? 'bg-orange-500/25 border-orange-500 text-orange-300' : 'bg-slate-900 border-borderDim text-textMain hover:bg-slate-800'}`}
            >
              {aoiActive ? "Cancel Custom AOI" : t.aoi}
            </button>
          </div>

          {/* Dynamic Legend */}
          <div className="glass-panel p-5 rounded-2xl border border-borderDim space-y-3">
            <h3 className="text-xs font-bold text-textMain border-b border-slate-900 pb-2 uppercase tracking-wide">{t.legend}</h3>
            
            <div className="space-y-2 text-[10px] font-semibold text-textMuted">
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded bg-red-600/70" />
                <span>Extreme Inundation Risk (&gt;75%)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded bg-orange-500/70" />
                <span>High Susceptibility (50-75%)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded bg-yellow-500/70" />
                <span>Moderate Risk (25-50%)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded bg-brown-600 bg-[#800000]/70" />
                <span>Hillside landslide threat</span>
              </div>
            </div>
          </div>

          {/* Ruler output details */}
          {measuredDistance !== null && (
            <div className="glass-panel p-4 rounded-xl border border-blue-500/30 bg-blue-950/20 text-xs space-y-1 animate-pulse">
              <span className="text-[10px] font-black uppercase text-blue-400">Ruler tool result:</span>
              <span className="text-sm font-black text-textMain block">{measuredDistance.toFixed(2)} km</span>
            </div>
          )}
        </div>

        {/* Right Main Map Container */}
        <div className="lg:col-span-3 glass-panel p-4 rounded-2xl border border-borderDim flex flex-col h-[580px] relative">
          {loading && (
            <div className="absolute inset-0 bg-[#050811]/60 backdrop-blur-sm z-[1000] flex items-center justify-center">
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          )}
          
          <div id="gis-map-viewport" className="w-full h-full rounded-xl border border-slate-950 z-10 relative" />

          {/* Active AOI Draw logic */}
          <AOIDrawer mapInstance={mapRef.current} onAOIDrawn={handleAOIDrawn} isActive={aoiActive} />

          {/* Flood/Landslide overlays */}
          {heatmapData && (
            <>
              <FloodHeatmap mapInstance={mapRef.current} heatmapData={heatmapData} visible={showFloodHeatmap} />
              <LandslideOverlay mapInstance={mapRef.current} heatmapData={heatmapData} visible={showLandslideOverlay} />
            </>
          )}

          {/* AOI Status Banner */}
          {aoiBounds && (
            <div className="absolute bottom-6 left-6 z-20 glass-panel p-3 rounded-lg border border-borderDim text-[9px] max-w-xs font-mono space-y-1">
              <span className="font-bold text-gray-300 block mb-0.5">AOI Segment Coordinates:</span>
              <span>N: {aoiBounds.max_lat.toFixed(4)}, S: {aoiBounds.min_lat.toFixed(4)}</span>
              <span className="block">E: {aoiBounds.max_lon.toFixed(4)}, W: {aoiBounds.min_lon.toFixed(4)}</span>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
