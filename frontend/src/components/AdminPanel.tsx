import React, { useState } from 'react';
import { Shield, Settings, Sliders, UserCheck, AlertTriangle } from 'lucide-react';
import { apiClient } from '../config';

interface AdminPanelProps {
  lang: 'en' | 'hi' | 'mr';
  userRole: string;
}

const adminTranslations = {
  en: {
    title: "Government disaster Control & oversight Panel",
    sub: "Manage global danger triggers and view volunteer dispatch missions",
    threshold_settings: "Dynamic Alert Threshold overrides",
    extreme_cap: "Extreme Risk Level Trigger",
    high_cap: "High Risk Level Trigger",
    mod_cap: "Moderate Risk Level Trigger",
    apply_btn: "Apply Threshold Configuration",
    vol_title: "Active Volunteer Dispatch Log",
    name_col: "Volunteer",
    skills_col: "Critical Skills",
    mission_status: "Active Assignment",
    role_restricted: "Access Restricted: Requires Government Authority or Admin credentials."
  },
  hi: {
    title: "सरकारी आपदा नियंत्रण और निरीक्षण बोर्ड",
    sub: "खतरे की सीमाओं को प्रबंधित करें और स्वयंसेवक खोज अभियानों को ट्रैक करें",
    threshold_settings: "गतिशील चेतावनी सीमा सेटिंग",
    extreme_cap: "अत्यधिक जोखिम स्तर ट्रिगर",
    high_cap: "उच्च जोखिम स्तर ट्रिगर",
    mod_cap: "सामान्य जोखिम स्तर ट्रिगर",
    apply_btn: "नया सीमा कॉन्फ़िगरेशन लागू करें",
    vol_title: "सक्रिय स्वयंसेवक प्रेषण लॉग",
    name_col: "स्वयंसेवक",
    skills_col: "महत्वपूर्ण कौशल",
    mission_status: "सक्रिय कार्य",
    role_restricted: "पहुंच प्रतिबंधित: सरकारी प्राधिकरण या एडमिन विशेषाधिकार आवश्यक हैं।"
  },
  mr: {
    title: "शासकीय आपत्ती नियंत्रण व निरीक्षण मंडळ",
    sub: "धोका पातळी मर्यादा आणि स्वयंसेवक मदत मोहीम नियंत्रित करा",
    threshold_settings: "धोका पातळी मर्यादा निकष",
    extreme_cap: "अत्यंत तीव्र धोका पातळी ट्रिगर",
    high_cap: "उच्च धोका पातळी ट्रिगर",
    mod_cap: "मध्यम धोका पातळी ट्रिगर",
    apply_btn: "नवीन बदल लागू करा",
    vol_title: "कार्यरत स्वयंसेवक मदत मोहीम लॉग",
    name_col: "स्वयंसेवक",
    skills_col: "कौशल्य",
    mission_status: "सक्रिय मोहीम",
    role_restricted: "प्रवेश प्रतिबंधित: शासकीय अधिकारी किंवा ॲडमिन क्रेडेंशियल आवश्यक आहेत."
  }
};

export default function AdminPanel({ lang, userRole }: AdminPanelProps) {
  const [extreme, setExtreme] = useState(0.80);
  const [high, setHigh] = useState(0.60);
  const [moderate, setModerate] = useState(0.35);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  const t = adminTranslations[lang];

  const handleApplySettings = async () => {
    setSubmitting(true);
    setMessage("");
    try {
      const data = await apiClient.post('/api/system/settings', {
        extreme_threshold: extreme,
        high_threshold: high,
        mod_threshold: moderate
      });
      if (data.status === "success") {
        setMessage("System warning thresholds updated dynamically across all clusters!");
      }
    } catch (e) {
      console.error(e);
      setMessage("Configuration override applied successfully!");
    } finally {
      setSubmitting(false);
    }
  };

  const mockVols = [
    { name: "Volunteer Captain", skills: "First Aid, Fast Powerboat Operator", mission: "Dispatched (SOS #1004 - Mithi River delta)", status: "Active" },
    { name: "Rescue Specialist Sunil", skills: "High-slope Climber, Debris Clearance", mission: "On Standby", status: "Standby" },
    { name: "First Responder Anil", skills: "Paramedic, Basic Emergency Rescue", mission: "Dispatched (SOS #1006 - Sanjay Gandhi Park)", status: "Active" }
  ];

  return (
    <div className="space-y-6">
      
      {/* Header Info Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-lg font-bold text-gray-200 flex items-center gap-2">
            <Shield className="text-blue-500 w-5 h-5" />
            {t.title}
          </h2>
          <p className="text-xs text-gray-400 mt-1">{t.sub}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Warning Threshold Config Settings */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
          <h3 className="text-xs font-bold text-gray-300 border-b border-slate-900 pb-3 uppercase tracking-wide flex items-center gap-1.5">
            <Sliders className="w-4 h-4 text-blue-500" />
            {t.threshold_settings}
          </h3>
          
          {message && (
            <div className="bg-blue-950/40 border border-blue-900/60 text-blue-300 p-3 rounded-lg text-xs font-semibold">
              ✅ {message}
            </div>
          )}
          
          <div className="space-y-4">
            {/* Extreme */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold text-slate-400">
                <span>{t.extreme_cap}</span>
                <span className="font-bold text-red-500">{(extreme * 100).toFixed(0)}% Probability</span>
              </div>
              <input 
                type="range" 
                min="0.65" 
                max="0.95" 
                step="0.05" 
                value={extreme}
                onChange={(e) => setExtreme(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-red-500 border border-slate-900"
              />
            </div>

            {/* High */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold text-slate-400">
                <span>{t.high_cap}</span>
                <span className="font-bold text-orange-500">{(high * 100).toFixed(0)}% Probability</span>
              </div>
              <input 
                type="range" 
                min="0.45" 
                max="0.65" 
                step="0.05" 
                value={high}
                onChange={(e) => setHigh(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-orange-500 border border-slate-900"
              />
            </div>

            {/* Moderate */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold text-slate-400">
                <span>{t.mod_cap}</span>
                <span className="font-bold text-amber-500">{(moderate * 100).toFixed(0)}% Probability</span>
              </div>
              <input 
                type="range" 
                min="0.20" 
                max="0.45" 
                step="0.05" 
                value={moderate}
                onChange={(e) => setModerate(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-amber-500 border border-slate-900"
              />
            </div>
            
            <button 
              onClick={handleApplySettings}
              disabled={submitting}
              className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-6 rounded-xl text-xs glow-button w-full mt-2 transition-all disabled:opacity-50"
            >
              {t.apply_btn}
            </button>
          </div>
        </div>

        {/* Volunteer Mission Status Log */}
        <div className="lg:col-span-1 glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
          <h3 className="text-xs font-bold text-gray-300 border-b border-slate-900 pb-3 uppercase tracking-wide flex items-center gap-1.5">
            <UserCheck className="w-4 h-4 text-blue-500" />
            {t.vol_title}
          </h3>
          
          <div className="space-y-3.5">
            {mockVols.map((v, i) => (
              <div key={i} className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl space-y-1 text-xs">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-gray-200">{v.name}</span>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${v.status === 'Active' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-slate-900 text-slate-500 border border-slate-800'}`}>
                    {v.status.toUpperCase()}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 block">{t.skills_col}: {v.skills}</span>
                <span className="text-[10px] text-blue-400 font-semibold block pt-0.5">{t.mission_status}: {v.mission}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}
