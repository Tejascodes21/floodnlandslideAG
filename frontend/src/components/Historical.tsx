import React, { useState } from 'react';
import { History, Play, Pause, Calendar, TrendingUp } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface HistoricalProps {
  lang: 'en' | 'hi' | 'mr';
}

const historicalTranslations = {
  en: {
    title: "Historical disaster Playback & Analytics",
    sub: "Analyze rolling 30-day weather histories, water expansion curves and hazard cycles",
    chart1: "Precipitation Accumulation vs hazard Risk (30-Day Timeline)",
    chart2: "NDWI Surface Water Index Saturation Curve",
    playback_title: "Sentinel Playback: Storm impact comparison",
    stage_before: "Before Storm (Dry ground, NDWI=-0.4)",
    stage_during: "During peak Storm (Inundated river basins, NDWI=0.35)",
    stage_after: "After Storm (Receding waters, high soil saturation)",
    timeline_speed: "Playback Speed",
    active_trends: "Critical Geospatial Trends"
  },
  hi: {
    title: "ऐतिहासिक आपदा प्लेबैक और विश्लेषण",
    sub: "३०-दिन के मौसम के इतिहास, जल विस्तार वक्र और खतरे के चक्रों का विश्लेषण करें",
    chart1: "वर्षा संचय बनाम जोखिम प्रतिशत (३०-दिवसीय समयरेखा)",
    chart2: "NDWI सतह जल सूचकांक संतृप्ति वक्र",
    playback_title: "सेंटिनल प्लेबैक: तूफान प्रभाव तुलना",
    stage_before: "तूफान से पहले (सूखी जमीन, NDWI=-0.4)",
    stage_during: "तूफान के दौरान (बाढ़ग्रस्त बेसिन, NDWI=0.35)",
    stage_after: "तूफान के बाद (घटता पानी, अत्यधिक गीली मिट्टी)",
    timeline_speed: "प्लेबैक गति",
    active_trends: "महत्वपूर्ण भू-स्थानिक रुझान"
  },
  mr: {
    title: "ऐतिहासिक आपत्ती विश्लेषण आणि प्लेबॅक",
    sub: "३०-दिवसांचा हवामान इतिहास, जल विस्तार वक्र आणि आपत्ती आवर्तनांचे विश्लेषण करा",
    chart1: "मुसळधार पाऊस विरुद्ध आपत्ती धोका (३०-दिवसीय आलेख)",
    chart2: "NDWI पाण्याचा फुगवटा निर्देशांक आलेख",
    playback_title: "सेंटिनेल प्लेबॅक: वादळ प्रभाव तुलना",
    stage_before: "वादळापूर्वी (कोरडी जमीन, NDWI=-0.4)",
    stage_during: "वादळ सुरू असताना (पूरग्रस्त खोरे, NDWI=0.35)",
    stage_after: "वादळानंतर (ओसरणारे पाणी, ओली माती)",
    timeline_speed: "प्लेबॅक वेग",
    active_trends: "भौगोलिक बदल कल"
  }
};

// Generate 30-day chronological historical datasets
const generateHistoricalData = () => {
  const data = [];
  const today = new Date();
  
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    
    // Simulate a severe storm peaking on day 15
    const isPeakStorm = i >= 12 && i <= 17;
    const rain = isPeakStorm ? 45 + Math.random() * 80 : Math.random() * 8;
    
    const floodRisk = isPeakStorm ? 70 + (rain / 125) * 28 : 10 + Math.random() * 15;
    const ndwi = isPeakStorm ? 0.2 + (rain / 125) * 0.4 : -0.55 + Math.random() * 0.15;
    const soilMoisture = isPeakStorm ? 80 + Math.random() * 15 : 25 + Math.random() * 15;
    
    data.push({
      date: d.toISOString().split('T')[0].slice(5),
      rain_mm: parseFloat(rain.toFixed(1)),
      risk_percentage: parseFloat(Math.min(100, floodRisk).toFixed(1)),
      ndwi: parseFloat(ndwi.toFixed(3)),
      soil_moisture: parseFloat(soilMoisture.toFixed(1))
    });
  }
  return data;
};

export default function Historical({ lang }: HistoricalProps) {
  const [data] = useState(generateHistoricalData());
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackStage, setPlaybackStage] = useState<'before' | 'during' | 'after'>('before');
  
  const t = historicalTranslations[lang];

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
    if (!isPlaying) {
      // Loop stages automatically
      let stages: ('before' | 'during' | 'after')[] = ['before', 'during', 'after'];
      let idx = 0;
      const interval = setInterval(() => {
        setPlaybackStage(stages[idx]);
        idx = (idx + 1) % 3;
      }, 1500);
      (window as any).playbackInterval = interval;
    } else {
      clearInterval((window as any).playbackInterval);
    }
  };

  const getPlaybackGrid = () => {
    // Generates localized visuals representing spatial change
    if (playbackStage === 'before') {
      return (
        <div className="w-full h-full flex flex-col justify-center items-center bg-[#070b12] text-xs gap-3 p-4 rounded-xl border border-slate-900">
          <div className="w-24 h-24 rounded-full bg-emerald-950/30 border-2 border-emerald-800/20 flex items-center justify-center font-black text-emerald-500">NDWI: -0.52</div>
          <span className="font-semibold text-gray-300">{t.stage_before}</span>
        </div>
      );
    }
    if (playbackStage === 'during') {
      return (
        <div className="w-full h-full flex flex-col justify-center items-center bg-[#051625] text-xs gap-3 p-4 rounded-xl border border-blue-900/40">
          <div className="w-24 h-24 rounded-full bg-cyan-600/30 border-2 border-cyan-500 flex items-center justify-center font-black text-cyan-400 pulse-threat">NDWI: 0.42</div>
          <span className="font-bold text-red-400 animate-pulse">{t.stage_during}</span>
        </div>
      );
    }
    return (
      <div className="w-full h-full flex flex-col justify-center items-center bg-[#0c1214] text-xs gap-3 p-4 rounded-xl border border-slate-900">
        <div className="w-24 h-24 rounded-full bg-blue-900/20 border-2 border-blue-900/50 flex items-center justify-center font-black text-blue-300">NDWI: -0.15</div>
        <span className="font-semibold text-gray-300">{t.stage_after}</span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Header Info Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-lg font-bold text-gray-200 flex items-center gap-2">
            <History className="text-blue-500 w-5 h-5" />
            {t.title}
          </h2>
          <p className="text-xs text-gray-400 mt-1">{t.sub}</p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900 px-3 py-1 rounded-lg border border-slate-800">
          <Calendar className="w-4 h-4 text-blue-500" />
          <span>Chronological Playback Active</span>
        </div>
      </div>

      {/* Main Charts Deck */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Chart 1: Rain vs Risk */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
          <h3 className="text-xs font-bold text-gray-300 border-b border-slate-900 pb-3 mb-4 uppercase tracking-wide flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            {t.chart1}
          </h3>
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#121826" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={9} />
                <YAxis stroke="#64748b" fontSize={9} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#090d16', border: '1px solid rgba(59, 130, 246, 0.2)' }}
                  itemStyle={{ color: '#f1f5f9', fontSize: '10px' }}
                />
                <Legend wrapperStyle={{ fontSize: '10px' }} />
                <Line type="monotone" dataKey="rain_mm" stroke="#3b82f6" strokeWidth={2.5} name="Rainfall (mm)" dot={false} />
                <Line type="monotone" dataKey="risk_percentage" stroke="#ef4444" strokeWidth={2.5} name="Calculated Risk (%)" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: NDWI Saturation */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
          <h3 className="text-xs font-bold text-gray-300 border-b border-slate-900 pb-3 mb-4 uppercase tracking-wide flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-cyan-500" />
            {t.chart2}
          </h3>
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                <defs>
                  <linearGradient id="colorNdwi" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#121826" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={9} />
                <YAxis stroke="#64748b" fontSize={9} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#090d16', border: '1px solid rgba(6, 182, 212, 0.2)' }}
                  itemStyle={{ color: '#f1f5f9', fontSize: '10px' }}
                />
                <Legend wrapperStyle={{ fontSize: '10px' }} />
                <Area type="monotone" dataKey="ndwi" stroke="#06b6d4" strokeWidth={2.5} fillOpacity={1} fill="url(#colorNdwi)" name="NDWI Water Area" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Before/During/After Playback Slider */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
        <div className="flex justify-between items-center mb-4 border-b border-slate-900 pb-3">
          <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wide">{t.playback_title}</h3>
          
          {/* Controls button */}
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              <button 
                onClick={() => setPlaybackStage('before')}
                className={`px-3 py-1 rounded-lg text-[10px] font-bold border transition-all ${playbackStage === 'before' ? 'bg-slate-900 border-slate-800 text-blue-400' : 'bg-slate-950 border-slate-900 text-slate-500'}`}
              >
                Before
              </button>
              <button 
                onClick={() => setPlaybackStage('during')}
                className={`px-3 py-1 rounded-lg text-[10px] font-bold border transition-all ${playbackStage === 'during' ? 'bg-red-950/20 border-red-900 text-red-400' : 'bg-slate-950 border-slate-900 text-slate-500'}`}
              >
                During
              </button>
              <button 
                onClick={() => setPlaybackStage('after')}
                className={`px-3 py-1 rounded-lg text-[10px] font-bold border transition-all ${playbackStage === 'after' ? 'bg-slate-900 border-slate-800 text-blue-300' : 'bg-slate-950 border-slate-900 text-slate-500'}`}
              >
                After
              </button>
            </div>
            
            <button 
              onClick={togglePlayback}
              className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-1 px-4 rounded-lg text-[10px] flex items-center gap-1.5 glow-button"
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              {isPlaying ? 'Pause Loop' : 'Play Timeline'}
            </button>
          </div>
        </div>
        
        {/* Playback Viewport */}
        <div className="w-full h-[220px]">
          {getPlaybackGrid()}
        </div>
      </div>

    </div>
  );
}
