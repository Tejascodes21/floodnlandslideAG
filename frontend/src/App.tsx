import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Map, 
  Satellite, 
  BarChart3, 
  Activity, 
  Radio, 
  UserSquare2, 
  LogOut, 
  Globe,
  Flame,
  AlertOctagon,
  AlertTriangle,
  HeartHandshake,
  Settings as SettingsIcon,
  BookOpen,
  Search,
  Sliders,
  Sun,
  Moon
} from 'lucide-react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import Dashboard from './components/Dashboard';
import GeoAIDashboard from './components/GeoAIDashboard';
import Analytics from './components/Analytics';
import MLPrediction from './components/MLPrediction';
import CommunityReports from './components/CommunityReports';
import VolunteerNetwork from './components/VolunteerNetwork';
import DisasterGuidelines from './components/DisasterGuidelines';
import Settings from './components/Settings';
import ApiStatus from './components/ApiStatus';
import SOSSystem from './components/SOSSystem';
import AIAssistant from './components/AIAssistant';
import GlobalSearch from './components/GlobalSearch';
import NotificationCenter from './components/NotificationCenter';
import ErrorBoundary from './components/shared/ErrorBoundary';

// Create a single global React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
      staleTime: 1000 * 30, // 30s
    },
  },
});

// Multi-language Translation Dictionaries
const translations = {
  en: {
    app_title: "GeoShield AI",
    tagline: "Emergency Operations Center & GeoAI Risk Deck",
    nav_dashboard: "Command Center Overview",
    nav_geoai: "GIS Workstation",
    nav_analytics: "Advanced Analytics",
    nav_ml: "AI Workspace",
    nav_reports: "Incident Reports",
    nav_volunteers: "Volunteer Network",
    nav_guidelines: "Response Guidelines",
    nav_apistatus: "Microservice Status",
    nav_settings: "EOC Configuration",
    nav_sos: "SOS Distress Desk",
    marquee_title: "ACTIVE SYSTEM ALERTS",
    marquee_msg: "Monsoon cyclonic weather detected in Western Ghats. Heavy rain triggers high soil moisture saturation risk. Citizen alert active.",
    login_title: "GeoShield AI Security Entry",
    login_sub: "Geospatial Emergency Control System",
    username: "Username",
    password: "Password",
    role: "Target System Role",
    login_btn: "Initialize Console",
    logout: "Exit Session",
    credentials_tip: "Fast Testing Credentials: login with username 'citizen', 'volunteer', 'ngo', 'govt' or 'admin' with password 'password123'."
  },
  hi: {
    app_title: "जियोशील्ड एआई",
    tagline: "आपातकालीन संचालन केंद्र और भू-स्थानिक जोखिम डेक",
    nav_dashboard: "कमांड सेंटर अवलोकन",
    nav_geoai: "जीआईएस वर्कस्टेशन",
    nav_analytics: "उन्नत विश्लेषण",
    nav_ml: "एआई वर्कस्पेस",
    nav_reports: "घटना रिपोर्ट",
    nav_volunteers: "स्वयंसेवक नेटवर्क",
    nav_guidelines: "प्रतिक्रिया दिशानिर्देश",
    nav_apistatus: "माइक्रोसर्विस स्थिति",
    nav_settings: "ईओसी कॉन्फ़िगरेशन",
    nav_sos: "एसओएस संकट प्रणाली",
    marquee_title: "सक्रिय प्रणाली चेतावनियाँ",
    marquee_msg: "पश्चिमी घाट में मानसूनी चक्रवाती मौसम दर्ज। भारी वर्षा से मिट्टी की नमी का अत्यधिक संतृप्ति जोखिम। नागरिक सतर्क रहें।",
    login_title: "जियोशील्ड एआई सुरक्षा प्रवेश",
    login_sub: "भू-स्थानिक आपातकालीन नियंत्रण प्रणाली",
    username: "उपयोगकर्ता नाम",
    password: "पासवर्ड",
    role: "लक्षित प्रणाली भूमिका",
    login_btn: "कंसोल आरंभ करें",
    logout: "सत्र समाप्त करें",
    credentials_tip: "त्वरित परीक्षण क्रेडेंशियल: यूजरनेम 'citizen', 'volunteer', 'ngo', 'govt' या 'admin' और पासवर्ड 'password123' डालें।"
  },
  mr: {
    app_title: "जिओशील्ड एआय",
    tagline: "आपत्कालीन संचालन कक्ष आणि जिओ-रिस्क डेक",
    nav_dashboard: "कमांड सेंटर विहंगावलोकन",
    nav_geoai: "जीआयएस वर्कस्टेशन",
    nav_analytics: "प्रगत विश्लेषण",
    nav_ml: "एआय वर्कस्पेस",
    nav_reports: "घटना अहवाल",
    nav_volunteers: "स्वयंसेवक नेटवर्क",
    nav_guidelines: "आपत्ती मार्गदर्शक तत्त्वे",
    nav_apistatus: "मायक्रोसर्व्हिस स्थिती",
    nav_settings: "ईओसी कॉन्फिगरेशन",
    nav_sos: "एसओएस संकट प्रणाली",
    marquee_title: "सक्रिय धोक्याची चेतावणी",
    marquee_msg: "पश्चिम घाटात मान्सून वादळी हवामानाची नोंद. मुसळधार पावसामुळे मातीची आर्द्रता वाढून दरडी कोसळण्याचा धोका. नागरिक दक्ष राहण्याचे आवाहन.",
    login_title: "जिओशील्ड एआय सुरक्षा प्रवेश",
    login_sub: "भू-स्थानिक आपत्कालीन नियंत्रण कक्ष",
    username: "वापरकर्ता नाव",
    password: "पासवर्ड",
    role: "लक्षित प्रणाली भूमिका",
    login_btn: "कंसोल सुरु करा",
    logout: "सत्र समाप्त करा",
    credentials_tip: "जलद चाचणी क्रेडेंशियल: वापरकर्ता नाव 'citizen', 'volunteer', 'ngo', 'govt' किंवा 'admin' आणि पासवर्ड 'password123' सह लॉगिन करा."
  }
};

function App() {
  const [lang, setLang] = useState<'en' | 'hi' | 'mr'>('en');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userRole, setUserRole] = useState("Citizen");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  
  // Center map/views coordinate context
  const [selectedCoord, setSelectedCoord] = useState<{ lat: number, lon: number, name: string } | null>(null);

  const t = translations[lang];

  // Effect to toggle CSS theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    const rolesMap: Record<string, string> = {
      "citizen": "Citizen",
      "volunteer": "Volunteer",
      "ngo": "NGO",
      "govt": "Government Authority",
      "admin": "Admin"
    };

    if (password === "password123" && rolesMap[username.toLowerCase()]) {
      setUserRole(rolesMap[username.toLowerCase()]);
      setIsLoggedIn(true);
    } else {
      setError("Incorrect password or invalid demo username. Read instructions below.");
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUsername("");
    setPassword("");
  };

  const handleSelectLocation = (lat: number, lon: number, name: string) => {
    setSelectedCoord({ lat, lon, name });
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bgDark px-4 py-8 relative overflow-hidden">
        {/* Glow Spheres */}
        <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] rounded-full bg-blue-900/10 blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-red-900/10 blur-[120px] pointer-events-none"></div>
        
        <div className="w-full max-w-md glass-panel p-8 rounded-2xl border border-borderGlow shadow-glass relative z-10">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-2">
              <ShieldAlert className="text-blue-500 w-8 h-8 pulse-threat" />
              <span className="font-extrabold text-2xl tracking-tight bg-gradient-to-r from-blue-400 to-red-400 bg-clip-text text-transparent">GeoShield AI</span>
            </div>
            
            {/* Language Selection */}
            <div className="flex items-center gap-1.5 bg-slate-900/80 dark:bg-slate-950/40 px-2 py-1 rounded-lg border border-borderDim text-xs">
              <Globe className="w-3.5 h-3.5 text-slate-400" />
              <select 
                value={lang} 
                onChange={(e) => setLang(e.target.value as any)} 
                className="bg-transparent text-textMain font-semibold focus:outline-none cursor-pointer"
              >
                <option value="en" className="bg-[#0b0f19]">EN</option>
                <option value="hi" className="bg-[#0b0f19]">HI</option>
                <option value="mr" className="bg-[#0b0f19]">MR</option>
              </select>
            </div>
          </div>
          
          <div className="text-center mb-6">
            <h2 className="text-lg font-bold text-textMain">{t.login_title}</h2>
            <p className="text-xs text-textMuted mt-1">{t.login_sub}</p>
          </div>

          {error && (
            <div className="mb-4 bg-red-950/40 border border-red-800/80 text-red-300 px-3 py-2 rounded-lg text-xs flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-textMuted mb-1">{t.username}</label>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. admin or citizen" 
                required
                className="w-full bg-[#080d19]/80 border border-borderDim px-3.5 py-2 rounded-lg text-sm text-textMain focus:outline-none focus:border-blue-500 transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-textMuted mb-1">{t.password}</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••" 
                required
                className="w-full bg-[#080d19]/80 border border-borderDim px-3.5 py-2 rounded-lg text-sm text-textMain focus:outline-none focus:border-blue-500 transition-all"
              />
            </div>
            <button 
              type="submit" 
              className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-600 text-white font-bold py-2 px-4 rounded-lg text-sm glow-button transition-all"
            >
              {t.login_btn}
            </button>
          </form>
          
          <div className="mt-6 border-t border-borderDim pt-4 text-[10px] text-textMuted leading-relaxed bg-slate-950/30 p-3 rounded-lg border border-borderDim/30">
            <span className="font-bold text-blue-400 block mb-1">💡 Developer Instructions:</span>
            {t.credentials_tip}
          </div>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen flex flex-col bg-bgDark text-textMain">
        
        {/* 1. Emergency Alert Marquee Warning */}
        <div className="w-full bg-red-950/60 border-b border-red-800/50 text-red-300 text-xs px-4 py-1.5 flex items-center gap-3 relative z-30">
          <span className="font-extrabold bg-red-800 px-2 py-0.5 rounded text-[10px] text-white tracking-wider flex items-center gap-1 shrink-0">
            <Flame className="w-3 h-3 pulse-threat" />
            {t.marquee_title}
          </span>
          <div className="overflow-hidden relative w-full h-4">
            <div className="absolute whitespace-nowrap animate-[marquee_28s_linear_infinite] hover:[animation-play-state:paused] cursor-pointer text-gray-200 font-medium">
              {t.marquee_msg}
            </div>
          </div>
        </div>
        
        {/* 2. Global Top Nav Header */}
        <header className="w-full border-b border-borderDim bg-bgPanel/75 backdrop-blur-md px-6 py-4 flex justify-between items-center relative z-20">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-600 to-red-600 p-2 rounded-xl border border-borderGlow">
              <ShieldAlert className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="font-extrabold text-xl bg-gradient-to-r from-blue-400 to-red-400 bg-clip-text text-transparent tracking-tight">{t.app_title}</h1>
              <p className="text-[10px] text-textMuted tracking-wide">{t.tagline}</p>
            </div>
          </div>

          {/* Search bar inside header */}
          <GlobalSearch lang={lang} onLocationSelect={handleSelectLocation} onNavigateTab={setActiveTab} />
          
          <div className="flex items-center gap-3.5">
            {/* Real-time Notifications */}
            <NotificationCenter lang={lang} onNotificationSelect={handleSelectLocation} />

            {/* Dark/Light mode toggle */}
            <button 
              onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
              className="p-2 bg-slate-900/80 hover:bg-slate-800 border border-borderDim rounded-xl text-slate-400 hover:text-gray-200 transition-all flex items-center justify-center cursor-pointer"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-blue-500" />}
            </button>

            {/* User Role Badge */}
            <div className="bg-slate-900/80 dark:bg-slate-950/30 px-3 py-1 rounded-full border border-borderDim flex items-center gap-2 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-textMuted font-medium">Role:</span>
              <span className="font-bold text-textMain">{userRole}</span>
            </div>
            
            {/* Language Selector */}
            <div className="flex items-center gap-1.5 bg-slate-900/80 dark:bg-slate-950/30 px-2 py-1 rounded-lg border border-borderDim text-xs">
              <Globe className="w-3.5 h-3.5 text-slate-400" />
              <select 
                value={lang} 
                onChange={(e) => setLang(e.target.value as any)} 
                className="bg-transparent text-textMain font-semibold focus:outline-none cursor-pointer"
              >
                <option value="en" className="bg-[#0b0f19]">EN</option>
                <option value="hi" className="bg-[#0b0f19]">HI</option>
                <option value="mr" className="bg-[#0b0f19]">MR</option>
              </select>
            </div>
            
            {/* Logout */}
            <button 
              onClick={handleLogout}
              title={t.logout}
              className="p-2 bg-slate-900/80 hover:bg-red-950/40 border border-borderDim hover:border-red-900/80 text-slate-400 hover:text-red-300 rounded-xl transition-all"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* 3. Main Dashboard Frame */}
        <div className="flex-1 flex overflow-hidden relative">
          
          {/* Sidebar Nav */}
          <aside className="w-64 border-r border-borderDim bg-[#070b13]/80 backdrop-blur-md flex flex-col justify-between py-6 px-4 shrink-0 z-20">
            <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-220px)]">
              <button 
                onClick={() => { setActiveTab("dashboard"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "dashboard" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <Map className="w-4 h-4" />
                {t.nav_dashboard}
              </button>
              
              <button 
                onClick={() => { setActiveTab("satellite"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "satellite" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <Satellite className="w-4 h-4" />
                {t.nav_geoai}
              </button>

              <button 
                onClick={() => { setActiveTab("historical"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "historical" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <BarChart3 className="w-4 h-4" />
                {t.nav_analytics}
              </button>

              <button 
                onClick={() => { setActiveTab("ml"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "ml" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <Activity className="w-4 h-4" />
                {t.nav_ml}
              </button>

              <button 
                onClick={() => { setActiveTab("reports"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "reports" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <AlertTriangle className="w-4 h-4" />
                {t.nav_reports}
              </button>

              <button 
                onClick={() => { setActiveTab("volunteers"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "volunteers" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <HeartHandshake className="w-4 h-4" />
                {t.nav_volunteers}
              </button>

              <button 
                onClick={() => { setActiveTab("guidelines"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "guidelines" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <BookOpen className="w-4 h-4" />
                {t.nav_guidelines}
              </button>

              <button 
                onClick={() => { setActiveTab("apistatus"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "apistatus" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <Radio className="w-4 h-4" />
                {t.nav_apistatus}
              </button>

              <button 
                onClick={() => { setActiveTab("settings"); setSelectedCoord(null); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${activeTab === "settings" ? 'bg-gradient-to-r from-blue-600/35 to-blue-500/10 border border-blue-500/40 text-blue-300 shadow-neon-blue/10' : 'hover:bg-slate-900/40 text-textMuted hover:text-textMain'}`}
              >
                <Sliders className="w-4 h-4" />
                {t.nav_settings}
              </button>
            </div>
            
            {/* SOS Distress Command shortcut */}
            <div className="border-t border-borderDim pt-4">
              <button 
                onClick={() => { setActiveTab("sos"); setSelectedCoord(null); }}
                className={`w-full flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl text-xs font-extrabold text-white tracking-widest uppercase transition-all glow-button-sos bg-gradient-to-r ${activeTab === "sos" ? 'from-red-600 to-red-500 border border-red-500/40 shadow-neon-red/30 pulse-threat' : 'from-red-700 to-red-800 hover:from-red-600 hover:to-red-500'}`}
              >
                <ShieldAlert className="w-4 h-4" />
                {t.nav_sos}
              </button>
            </div>
          </aside>
          
          {/* Central View Router */}
          <main className="flex-1 overflow-y-auto p-6 bg-bgDark relative z-10">
            <ErrorBoundary>
              {activeTab === "dashboard" && <Dashboard lang={lang} userRole={userRole} selectedLocation={selectedCoord} />}
              {activeTab === "satellite" && <GeoAIDashboard lang={lang} />}
              {activeTab === "historical" && <Analytics lang={lang} />}
              {activeTab === "ml" && <MLPrediction lang={lang} />}
              {activeTab === "reports" && <CommunityReports lang={lang} />}
              {activeTab === "volunteers" && <VolunteerNetwork lang={lang} />}
              {activeTab === "guidelines" && <DisasterGuidelines lang={lang} />}
              {activeTab === "apistatus" && <ApiStatus lang={lang} />}
              {activeTab === "settings" && <Settings lang={lang} userRole={userRole} onChangeRole={setUserRole} />}
              {activeTab === "sos" && <SOSSystem lang={lang} userRole={userRole} />}
            </ErrorBoundary>
          </main>
          
          {/* Floating Contextual AIAssistant Chat copilot drawer */}
          <AIAssistant lang={lang} currentTab={activeTab} />
        </div>
        
        {/* Styling marquee animation */}
        <style>{`
          @keyframes marquee {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
          }
        `}</style>
      </div>
    </QueryClientProvider>
  );
}

export default App;
