import React, { useState } from 'react';
import { History, Play, Pause, Calendar, TrendingUp, AlertTriangle, CloudRain, Droplet, Layers } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import TimelinePlayer from './TimelinePlayer';

interface AnalyticsProps {
  lang: 'en' | 'hi' | 'mr';
}

const analyticsTranslations = {
  en: {
    title: "Advanced Geospatial Analytics",
    sub: "Analyze rolling weather histories, water expansion curves and hazard anomaly trends",
    chart1: "Precipitation Accumulation vs Hazard Risk Index",
    chart2: "NDWI Surface Water Index Saturation Curve",
    playback_title: "Sentinel Playback: Storm Impact Timeline",
    playback_sub: "Review satellite sensors telemetry variations chronologically",
    kpi_rainfall: "Peak Rainfall (24h)",
    kpi_moisture: "Mean Soil Saturation",
    kpi_anomalies: "Anomalies Detected",
    anomaly_alert: "PRECIPITATION SPIKE: Rainfall exceeded standard deviation on day 15.",
    filter_days: "Filtering: Past 30 Days",
    station_select: "Monitoring Station: Western Ghats Grid A"
  },
  hi: {
    title: "उन्नत भू-स्थानिक विश्लेषण",
    sub: "मौसम के इतिहास, जल विस्तार वक्र और खतरे की विसंगति प्रवृत्तियों का विश्लेषण करें",
    chart1: "वर्षा संचय बनाम जोखिम प्रतिशत समयरेखा",
    chart2: "NDWI सतह जल सूचकांक संतृप्ति वक्र",
    playback_title: "सेंटिनल प्लेबैक: तूफान प्रभाव समयरेखा",
    playback_sub: "कालानुक्रमिक रूप से उपग्रह सेंसर टेलीमेट्री बदलावों की समीक्षा करें",
    kpi_rainfall: "उच्चतम वर्षा (२४ घंटे)",
    kpi_moisture: "औसत मिट्टी संतृप्ति",
    kpi_anomalies: "विसंगतियां पाई गईं",
    anomaly_alert: "वर्षा वृद्धि: १५वें दिन सामान्य विचलन से अधिक वर्षा दर्ज की गई।",
    filter_days: "फ़िल्टरिंग: पिछले ३० दिन",
    station_select: "निगरानी स्टेशन: पश्चिमी घाट ग्रिड ए"
  },
  mr: {
    title: "प्रगत भौगोलिक विश्लेषण",
    sub: "हवामान इतिहास, पाण्याचा फुगवटा आलेख आणि आपत्ती अनियमिता कल तपासा",
    chart1: "मुसळधार पाऊस विरुद्ध आपत्ती धोका आलेख",
    chart2: "NDWI पाण्याचा फुगवटा निर्देशांक आलेख",
    playback_title: "सेंटिनेल प्लेबॅक: वादळ प्रभाव काळ",
    playback_sub: "उपग्रह सेन्सरमधील बदल कालानुक्रमे तपासा",
    kpi_rainfall: "कमाल पाऊस (२४ तास)",
    kpi_moisture: "सरासरी माती आर्द्रता",
    kpi_anomalies: "त्रुटी/विसंगती आढळल्या",
    anomaly_alert: "अतिवृष्टी इशारा: १५व्या दिवशी सरासरीपेक्षा जास्त पाऊस नोंदवला गेला.",
    filter_days: "कालमर्यादा: मागील ३० दिवस",
    station_select: "मॉनिटरिंग स्टेशन: पश्चिम घाट ग्रिड ए"
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

// Generate a 10-frame sequence for the TimelinePlayer
const generateSatelliteFrames = () => {
  return Array.from({ length: 10 }, (_, idx) => {
    const daysAgo = 10 - idx;
    // Storm peaks at around days_ago = 4
    const isStorm = daysAgo >= 3 && daysAgo <= 5;
    return {
      days_ago: daysAgo,
      ndwi: isStorm ? 0.38 + idx * 0.01 : -0.45 + (idx % 3) * 0.05,
      ndvi: isStorm ? 0.18 : 0.65 - (idx % 2) * 0.05,
      sar_vv_db: isStorm ? -6.2 : -14.5,
      soil_moisture: isStorm ? 92 : 38
    };
  });
};

export default function Analytics({ lang }: AnalyticsProps) {
  const [data] = useState(generateHistoricalData());
  const [satelliteFrames] = useState(generateSatelliteFrames());
  const [currentFrame, setCurrentFrame] = useState<any>(satelliteFrames[0]);
  const [selectedStation, setSelectedStation] = useState("Station-A");
  
  const t = analyticsTranslations[lang];

  return (
    <div className="space-y-6">
      
      {/* Header Info Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-borderDim flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-lg font-bold text-textMain flex items-center gap-2">
            <History className="text-blue-500 w-5 h-5" />
            {t.title}
          </h2>
          <p className="text-xs text-textMuted mt-1">{t.sub}</p>
        </div>
        
        {/* Interactive Filters */}
        <div className="flex gap-2 text-xs">
          <select 
            value={selectedStation} 
            onChange={(e) => setSelectedStation(e.target.value)}
            className="bg-slate-900 border border-borderDim text-textMain px-3 py-1.5 rounded-lg focus:outline-none"
          >
            <option value="Station-A">{t.station_select}</option>
            <option value="Station-B">Monitoring Station: Mumbai Hills Grid B</option>
          </select>
          <div className="flex items-center gap-1.5 text-textMuted bg-slate-900 px-3 py-1.5 rounded-lg border border-borderDim">
            <Calendar className="w-4 h-4 text-blue-500" />
            <span>{t.filter_days}</span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-borderDim flex justify-between items-center">
          <div>
            <span className="text-[10px] text-textMuted font-bold uppercase tracking-wider block">{t.kpi_rainfall}</span>
            <span className="text-2xl font-black text-blue-400 mt-1 block">118.5 mm</span>
          </div>
          <div className="p-2.5 bg-blue-500/10 border border-blue-500/30 text-blue-500 rounded-lg">
            <CloudRain className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-borderDim flex justify-between items-center">
          <div>
            <span className="text-[10px] text-textMuted font-bold uppercase tracking-wider block">{t.kpi_moisture}</span>
            <span className="text-2xl font-black text-amber-500 mt-1 block">54.2%</span>
          </div>
          <div className="p-2.5 bg-amber-500/10 border border-amber-500/30 text-amber-500 rounded-lg">
            <Droplet className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-borderDim flex justify-between items-center">
          <div>
            <span className="text-[10px] text-textMuted font-bold uppercase tracking-wider block">{t.kpi_anomalies}</span>
            <span className="text-2xl font-black text-red-500 mt-1 block">1 Alert</span>
          </div>
          <div className="p-2.5 bg-red-500/10 border border-red-500/30 text-red-500 rounded-lg">
            <AlertTriangle className="w-5 h-5 animate-pulse" />
          </div>
        </div>
      </div>

      {/* Anomaly Detection Banner */}
      <div className="p-3.5 rounded-xl border border-red-500/25 bg-red-950/20 text-red-300 text-xs flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 pulse-threat" />
        <span className="font-semibold">{t.anomaly_alert}</span>
      </div>

      {/* Recharts Charts Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Chart 1: Rainfall vs Risk */}
        <div className="glass-panel p-5 rounded-2xl border border-borderDim">
          <h3 className="text-xs font-bold text-textMain border-b border-slate-900 pb-3 mb-4 uppercase tracking-wide flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            {t.chart1}
          </h3>
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={9} />
                <YAxis stroke="#64748b" fontSize={9} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(59, 130, 246, 0.2)' }}
                  itemStyle={{ color: '#f1f5f9', fontSize: '10px' }}
                />
                <Legend wrapperStyle={{ fontSize: '10px' }} />
                <Line type="monotone" dataKey="rain_mm" stroke="#3b82f6" strokeWidth={2.5} name="Rainfall (mm)" dot={false} />
                <Line type="monotone" dataKey="risk_percentage" stroke="#ef4444" strokeWidth={2.5} name="Calculated Risk (%)" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: NDWI Area */}
        <div className="glass-panel p-5 rounded-2xl border border-borderDim">
          <h3 className="text-xs font-bold text-textMain border-b border-slate-900 pb-3 mb-4 uppercase tracking-wide flex items-center gap-1.5">
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
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={9} />
                <YAxis stroke="#64748b" fontSize={9} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(6, 182, 212, 0.2)' }}
                  itemStyle={{ color: '#f1f5f9', fontSize: '10px' }}
                />
                <Legend wrapperStyle={{ fontSize: '10px' }} />
                <Area type="monotone" dataKey="ndwi" stroke="#06b6d4" strokeWidth={2.5} fillOpacity={1} fill="url(#colorNdwi)" name="NDWI Water Area" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Timeline scrubbing player */}
      <div className="glass-panel p-5 rounded-2xl border border-borderDim">
        <div className="border-b border-slate-900 pb-3 mb-4">
          <h3 className="text-xs font-bold text-textMain uppercase tracking-wide flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-blue-500" />
            {t.playback_title}
          </h3>
          <p className="text-[10px] text-textMuted mt-0.5">{t.playback_sub}</p>
        </div>
        
        <TimelinePlayer timeseries={satelliteFrames} onFrameChange={setCurrentFrame} lang={lang} />
      </div>

    </div>
  );
}
