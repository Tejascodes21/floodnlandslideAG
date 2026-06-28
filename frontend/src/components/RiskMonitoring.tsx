import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu, CheckCircle } from 'lucide-react';

interface RiskMonitoringProps {
  lang: 'en' | 'hi' | 'mr';
}

const monitoringTranslations = {
  en: {
    title: "Telemetry Environmental Sensor Grid",
    sub: "Live feeds from regional river level gauges and slope moisture telemetries",
    river_title: "Hydrological river Level Stations",
    soil_title: "Hillside soil Moisture Probes",
    station_name: "Sensor Station",
    water_level: "Depth (m)",
    moisture: "Soil Saturation",
    status: "Telemetry Status",
    sensor_network: "Sensor Network status: OPERATIONAL"
  },
  hi: {
    title: "टेलीमेट्री पर्यावरण सेंसर ग्रिड",
    sub: "क्षेत्रीय नदी स्तर गेज और पहाड़ी नमी टेलीमेट्री से लाइव फीड",
    river_title: "जल विज्ञान नदी स्तर स्टेशन",
    soil_title: "पहाड़ी मिट्टी नमी जांच (Probes)",
    station_name: "सेंसर स्टेशन",
    water_level: "गहराई (मीटर)",
    moisture: "मिट्टी संतृप्ति",
    status: "टेलीमेट्री स्थिति",
    sensor_network: "सेंसर नेटवर्क स्थिति: परिचालन में (OPERATIONAL)"
  },
  mr: {
    title: "टेलेमेट्री पर्यावरण सेन्सर ग्रिड",
    sub: "नदी पाणी पातळी आणि डोंगरउतार माती आर्द्रता सेन्सरची थेट माहिती",
    river_title: "जलविज्ञान नदी पाणी पातळी केंद्र",
    soil_title: "डोंगरउतार माती आर्द्रता मोजमाप केंद्र",
    station_name: "सेन्सर केंद्र",
    water_level: "पाणी खोली (मीटर)",
    moisture: "माती पाणी पातळी",
    status: "टेलेमेट्री स्थिती",
    sensor_network: "सेन्सर नेटवर्क स्थिती: कार्यरत आहे (OPERATIONAL)"
  }
};

export default function RiskMonitoring({ lang }: RiskMonitoringProps) {
  const t = monitoringTranslations[lang];

  // Dynamic telemetry stations state with slight random variation to feel alive!
  const [riverStations, setRiverStations] = useState([
    { id: "R-101", name: "Mithi River Gauge Terminal A", depth: 3.4, threshold: 5.0, status: "Normal" },
    { id: "R-102", name: "Thane Creek Delta Sensor B", depth: 4.8, threshold: 5.5, status: "Elevated" },
    { id: "R-103", name: "Dahisar River Basin Monitor C", depth: 2.1, threshold: 4.5, status: "Normal" },
    { id: "R-104", name: "Ulhas River Catchment Sector D", depth: 6.7, threshold: 6.0, status: "Critical" }
  ]);

  const [soilProbes, setSoilProbes] = useState([
    { id: "S-501", location: "Ghatkopar Hill Slope Sector A", saturation: 84, threshold: 75, status: "High" },
    { id: "S-502", location: "Sanjay Gandhi Park Slope Sector B", saturation: 42, threshold: 75, status: "Normal" },
    { id: "S-503", location: "Lonavala Hill Pass Sector C", saturation: 89, threshold: 80, status: "Critical" },
    { id: "S-504", location: "Khandala Ridge Sector D", saturation: 56, threshold: 80, status: "Normal" }
  ]);

  useEffect(() => {
    // Add real-time fluctuation ticks
    const interval = setInterval(() => {
      setRiverStations(prev => 
        prev.map(s => {
          const delta = (Math.random() - 0.45) * 0.12;
          const newDepth = Math.max(0.5, parseFloat((s.depth + delta).toFixed(2)));
          let stat = "Normal";
          if (newDepth >= s.threshold) stat = "Critical";
          else if (newDepth >= s.threshold * 0.8) stat = "Elevated";
          return { ...s, depth: newDepth, status: stat };
        })
      );

      setSoilProbes(prev => 
        prev.map(p => {
          const delta = Math.floor((Math.random() - 0.48) * 3);
          const newSat = Math.min(99, Math.max(5, p.saturation + delta));

          let stat = "Normal";
          if (newSat >= p.threshold) stat = "Critical";
          else if (newSat >= p.threshold * 0.85) stat = "High";
          return { ...p, saturation: newSat, status: stat };
        })
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    if (status === "Critical") {
      return (
        <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded text-[10px] font-black uppercase pulse-threat flex items-center gap-1 w-fit">
          <ShieldAlert className="w-3 h-3" /> Critical
        </span>
      );
    }
    if (status === "Elevated" || status === "High") {
      return (
        <span className="bg-orange-500/20 text-orange-400 border border-orange-500/30 px-2 py-0.5 rounded text-[10px] font-bold uppercase flex items-center gap-1 w-fit">
          <Activity className="w-3 h-3 animate-pulse" /> High Risk
        </span>
      );
    }
    return (
      <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-bold uppercase flex items-center gap-1 w-fit">
        <CheckCircle className="w-3 h-3" /> Operational
      </span>
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Header Info Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-full satellite-scanner pointer-events-none"></div>
        <div>
          <h2 className="text-lg font-bold text-gray-200 flex items-center gap-2">
            <Cpu className="text-blue-500 w-5 h-5" />
            {t.title}
          </h2>
          <p className="text-xs text-gray-400 mt-1">{t.sub}</p>
          <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-bold bg-emerald-950/20 border border-emerald-950 px-3 py-1 rounded-lg mt-3 w-fit">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>{t.sensor_network}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* River Gauges */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
          <h3 className="text-xs font-bold text-gray-300 border-b border-slate-900 pb-3 mb-4 uppercase tracking-wide flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-blue-500" />
            {t.river_title}
          </h3>
          
          <div className="space-y-3">
            {riverStations.map((station) => (
              <div key={station.id} className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-900 flex justify-between items-center gap-4">
                <div>
                  <span className="text-[10px] text-slate-500 font-bold block">{station.id}</span>
                  <span className="text-xs font-bold text-gray-200">{station.name}</span>
                </div>
                <div className="flex items-center gap-6 shrink-0">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 block mb-0.5">{t.water_level}</span>
                    <span className="font-extrabold text-sm text-gray-300">{station.depth} / {station.threshold}m</span>
                  </div>
                  {getStatusBadge(station.status)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Hillside Probes */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
          <h3 className="text-xs font-bold text-gray-300 border-b border-slate-900 pb-3 mb-4 uppercase tracking-wide flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-orange-500" />
            {t.soil_title}
          </h3>
          
          <div className="space-y-3">
            {soilProbes.map((probe) => (
              <div key={probe.id} className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-900 flex justify-between items-center gap-4">
                <div>
                  <span className="text-[10px] text-slate-500 font-bold block">{probe.id}</span>
                  <span className="text-xs font-bold text-gray-200">{probe.location}</span>
                </div>
                <div className="flex items-center gap-6 shrink-0">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 block mb-0.5">{t.moisture}</span>
                    <span className="font-extrabold text-sm text-gray-300">{probe.saturation}%</span>
                  </div>
                  {getStatusBadge(probe.status)}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}
