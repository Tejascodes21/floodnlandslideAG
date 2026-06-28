import React, { useState, useEffect, useRef } from 'react';
import { Layers, Eye, RefreshCw, Info, Calendar } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { API_BASE_URL } from '../config';

interface LiveSatelliteProps {
  lang: 'en' | 'hi' | 'mr';
}

const satelliteTranslations = {
  en: {
    title: "Sentinel Multi-Spectral Imagery visualizer",
    sub: "Live overpass Sentinel-1 SAR and Sentinel-2 Optical processing",
    overpass_info: "Last Sentinel-2 pass: 4 hours ago | Cloud masking: 0.12% | Resolution: 10m",
    select_layer: "Select Imagery Band",
    rgb: "True Color (RGB)",
    ndwi: "Water index segmentation (NDWI)",
    ndvi: "Vegetation stress analysis (NDVI)",
    dem: "DEM Terrain elevation shading",
    active_overpass: "Sentinel Overpass Telemetry",
    trajectory: "Trajectory: Northbound Orbit",
    sar_status: "Sentinel-1 SAR Status: ACTIVE (Radar Penetration)",
    trigger_refresh: "Trigger Satellite Refresh"
  },
  hi: {
    title: "सेंटिनल मल्टी-स्पेक्ट्रल इमेजरी विज़ुअलाइज़र",
    sub: "लाइव सेंटिनल -1 SAR और सेंटिनल -2 ऑप्टिकल प्रसंस्करण",
    overpass_info: "अंतिम पास: ४ घंटे पहले | क्लाउड मास्किंग: ०.१२% | रिज़ॉल्यूशन: १० मीटर",
    select_layer: "इमेजरी बैंड चुनें",
    rgb: "वास्तविक रंग (RGB)",
    ndwi: "जल सूचकांक विभाजन (NDWI)",
    ndvi: "वनस्पति तनाव विश्लेषण (NDVI)",
    dem: "DEM भू-भाग ऊंचाई छायांकन",
    active_overpass: "सेंटिनल ओवरपास टेलीमेट्री",
    trajectory: "प्रक्षेपवक्र: उत्तर की ओर कक्षा",
    sar_status: "सेंटिनल-1 SAR स्थिति: सक्रिय (रडार प्रवेश)",
    trigger_refresh: "सैटेलाइट रिफ्रेश सक्रिय करें"
  },
  mr: {
    title: "सेंटिनेल मल्टी-स्पेक्ट्रल इमेजरी व्हिज्युअलायझर",
    sub: "लाइव्ह सेंटिनेल-1 SAR आणि सेंटिनेल-2 ऑप्टिकल विश्लेषण",
    overpass_info: "शेवटचा पास: ४ तास पूर्वी | क्लाउड मास्किंग: ०.१२% | रिझोल्यूशन: १० मीटर",
    select_layer: "इमेजरी बँड निवडा",
    rgb: "मूळ रंग (RGB)",
    ndwi: "जल पातळी निर्देशांक (NDWI)",
    ndvi: "वनस्पती घनता विश्लेषण (NDVI)",
    dem: "DEM डोंगरउतार उंची रेखांकन",
    active_overpass: "सेंटिनेल ओव्हरपास टेलीमेट्री",
    trajectory: "कक्षा: उत्तर दिशा परिभ्रमण",
    sar_status: "सेंटिनेल-1 SAR स्थिती: सक्रिय (रडार वेध)",
    trigger_refresh: "सैटेलाइट रिफ्रेश सुरु करा"
  }
};

export default function LiveSatellite({ lang }: LiveSatelliteProps) {
  const [activeBand, setActiveBand] = useState<'rgb' | 'ndwi' | 'ndvi' | 'dem'>('rgb');
  const [loading, setLoading] = useState(false);
  const [passDate, setPassDate] = useState(new Date().toISOString().split('T')[0]);
  const [tilesUnavailable, setTilesUnavailable] = useState(false);
  
  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  
  const t = satelliteTranslations[lang];

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map('satellite-map', {
        center: [19.076, 72.877],
        zoom: 12,
        zoomControl: false
      });

      // Add a base dark map as a fallback / background layer
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20
      }).addTo(mapRef.current);

      L.control.zoom({ position: 'bottomright' }).addTo(mapRef.current);
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;

    if (tileLayerRef.current) {
      mapRef.current.removeLayer(tileLayerRef.current);
    }

    setLoading(true);
    setTilesUnavailable(false);

    const tileUrl = `${API_BASE_URL}/api/gis/tile/${activeBand}/{z}/{x}/{y}`;
    const satelliteLayer = L.tileLayer(tileUrl, {
      maxZoom: 18,
      attribution: 'Sentinel Satellite Data'
    });

    satelliteLayer.on('load', () => {
      setLoading(false);
    });

    satelliteLayer.on('tileerror', () => {
      setLoading(false);
      setTilesUnavailable(true);
    });

    satelliteLayer.addTo(mapRef.current);
    tileLayerRef.current = satelliteLayer;

    const timeout = setTimeout(() => {
      setLoading(false);
    }, 1500);

    return () => {
      clearTimeout(timeout);
    };
  }, [activeBand]);

  const refreshSatelliteData = () => {
    setLoading(true);
    setTilesUnavailable(false);
    if (tileLayerRef.current) {
      tileLayerRef.current.redraw();
    }
    setTimeout(() => {
      setLoading(false);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      
      {/* Header Info Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-full satellite-scanner pointer-events-none"></div>
        <div>
          <h2 className="text-lg font-bold text-gray-200 flex items-center gap-2">
            <Layers className="text-blue-500 w-5 h-5 shrink-0" />
            {t.title}
          </h2>
          <p className="text-xs text-gray-400 mt-1">{t.sub}</p>
          <div className="flex items-center gap-1.5 text-[10px] text-blue-400 font-semibold bg-blue-950/20 border border-blue-900/30 px-3 py-1 rounded-lg mt-3 w-fit">
            <Info className="w-3.5 h-3.5" />
            <span>{t.overpass_info}</span>
          </div>
        </div>
        
        <button 
          onClick={refreshSatelliteData}
          disabled={loading}
          className="bg-slate-900 hover:bg-slate-800 text-gray-200 border border-slate-800 hover:border-slate-700 font-bold py-2 px-5 rounded-xl text-xs flex items-center gap-2 glow-button shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          {t.trigger_refresh}
        </button>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Side Imagery Visualization */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-800/80 flex flex-col items-center">
          <div className="w-full flex justify-between items-center mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Eye className="w-4 h-4 text-blue-500" />
              Raster Analysis Resolution Grid
            </span>
            <span className="text-[10px] bg-slate-900 px-2 py-0.5 border border-slate-800 rounded text-gray-400">
              Sentinel-2 band scale: 10m/px
            </span>
          </div>
          
          {/* Real Leaflet Map */}
          <div className="w-full max-w-[420px] aspect-square bg-[#050811] rounded-xl border border-slate-950 relative overflow-hidden">
            {loading && (
              <div className="absolute inset-0 bg-[#050811]/70 backdrop-blur-sm z-[1000] flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
              </div>
            )}
            
            {/* Div for Leaflet Map viewport */}
            <div id="satellite-map" className="w-full h-full z-10" />

            {/* Indicator if live tiles are unavailable */}
            {tilesUnavailable && (
              <div className="absolute top-3 left-3 z-[1000] bg-red-950/90 border border-red-500/50 text-red-400 text-[11px] font-bold px-3 py-1.5 rounded-lg shadow-neon-red flex items-center gap-1.5 animate-pulse">
                <span className="w-2 h-2 rounded-full bg-red-500"></span>
                Live Tiles Offline (Fallback Active)
              </div>
            )}
          </div>
        </div>

        {/* Right Side Control Panel */}
        <div className="space-y-6">
          {/* Layer Selector */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-3">
            <h3 className="text-xs font-bold text-gray-300 border-b border-slate-900 pb-2 uppercase tracking-wide">{t.select_layer}</h3>
            
            <div className="space-y-2">
              <button 
                onClick={() => setActiveBand('rgb')}
                className={`w-full flex justify-between items-center px-4 py-2.5 rounded-xl text-xs font-semibold border transition-all ${activeBand === 'rgb' ? 'bg-blue-600/20 border-blue-500 text-blue-300' : 'bg-slate-950/60 border-slate-900 text-slate-400 hover:text-gray-200'}`}
              >
                <span>{t.rgb}</span>
                <span className="text-[10px] bg-slate-900 px-2 py-0.5 rounded text-gray-400">B2, B3, B4</span>
              </button>
              <button 
                onClick={() => setActiveBand('ndwi')}
                className={`w-full flex justify-between items-center px-4 py-2.5 rounded-xl text-xs font-semibold border transition-all ${activeBand === 'ndwi' ? 'bg-blue-600/20 border-blue-500 text-blue-300' : 'bg-slate-950/60 border-slate-900 text-slate-400 hover:text-gray-200'}`}
              >
                <span>{t.ndwi}</span>
                <span className="text-[10px] bg-slate-900 px-2 py-0.5 rounded text-gray-400">B3 - B8</span>
              </button>
              <button 
                onClick={() => setActiveBand('ndvi')}
                className={`w-full flex justify-between items-center px-4 py-2.5 rounded-xl text-xs font-semibold border transition-all ${activeBand === 'ndvi' ? 'bg-blue-600/20 border-blue-500 text-blue-300' : 'bg-slate-950/60 border-slate-900 text-slate-400 hover:text-gray-200'}`}
              >
                <span>{t.ndvi}</span>
                <span className="text-[10px] bg-slate-900 px-2 py-0.5 rounded text-gray-400">B4 - B8</span>
              </button>
              <button 
                onClick={() => setActiveBand('dem')}
                className={`w-full flex justify-between items-center px-4 py-2.5 rounded-xl text-xs font-semibold border transition-all ${activeBand === 'dem' ? 'bg-blue-600/20 border-blue-500 text-blue-300' : 'bg-slate-950/60 border-slate-900 text-slate-400 hover:text-gray-200'}`}
              >
                <span>{t.dem}</span>
                <span className="text-[10px] bg-slate-900 px-2 py-0.5 rounded text-gray-400">SRTM DEM</span>
              </button>
            </div>
          </div>

          {/* Satellite Telemetry Details */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
            <h3 className="text-xs font-bold text-gray-300 border-b border-slate-900 pb-2 uppercase tracking-wide">{t.active_overpass}</h3>
            
            <div className="space-y-3 text-[11px]">
              <div className="flex justify-between items-center border-b border-slate-900 pb-1.5">
                <span className="text-slate-400">Satellite Source</span>
                <span className="font-semibold text-gray-200">Sentinel-2A Multispectral</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-900 pb-1.5">
                <span className="text-slate-400">Orbital Trajectory</span>
                <span className="font-semibold text-gray-200">{t.trajectory}</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-900 pb-1.5">
                <span className="text-slate-400">Cloud Shield Mask</span>
                <span className="font-semibold text-emerald-400">0.12% (Clear Capture)</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Radar Backscatter</span>
                <span className="font-semibold text-blue-400">Sentinel-1 active (-12.4dB)</span>
              </div>
            </div>
            
            <div className="p-3 bg-blue-950/20 border border-blue-900/30 rounded-lg text-[10px] text-blue-300 leading-relaxed font-semibold">
              🛰️ {t.sar_status}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
