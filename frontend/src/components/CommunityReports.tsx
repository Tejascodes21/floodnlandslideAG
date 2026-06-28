import React, { useState, useEffect, useRef } from 'react';
import { ShieldAlert, Compass, MapPin, Eye, ThumbsUp, CheckCircle, Search, Sliders, AlertTriangle, PlusCircle, X } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import L from 'leaflet';
import { apiClient } from '../config';

interface CommunityReportsProps {
  lang: 'en' | 'hi' | 'mr';
}

const reportsTranslations = {
  en: {
    title: "Citizen incident Reporting Desk",
    sub: "Geotag regional flash points, report blocked evacuation routes, and verify flood zones",
    map_telemetry: "GIS Incident Cluster Map",
    filters_title: "Report Registry search",
    sub_btn: "Report New Incident",
    type: "Incident Category",
    details: "Description details",
    submit: "Broadcast Incident Report",
    reporter: "Reporter Name",
    upvotes: "Upvotes",
    status_lbl: "Verification Status",
    gps_click: "Click map to set GPS coordinates",
    cat_flood: "Flood Inundation",
    cat_landslide: "Landslide / Debris",
    cat_road: "Road Blockage",
    cat_power: "Power Outage",
    cat_other: "Other hazard",
    verify_btn: "Verify Report",
    resolve_btn: "Mark Resolved",
    success_msg: "Incident report submitted successfully!",
    all_types: "All Incident Categories",
    all_status: "All Statuses",
    no_reports: "No incident reports active in this sector."
  },
  hi: {
    title: "नागरिक घटना रिपोर्टिंग डेस्क",
    sub: "क्षेत्रीय फ्लैश बिंदुओं को जियोटैग करें, अवरुद्ध निकासी मार्गों की रिपोर्ट करें, और बाढ़ क्षेत्रों को सत्यापित करें",
    map_telemetry: "जीआईएस घटना क्लस्टर मानचित्र",
    filters_title: "रिपोर्ट रजिस्ट्री खोजें",
    sub_btn: "नई घटना की रिपोर्ट करें",
    type: "घटना श्रेणी",
    details: "घटना का विवरण",
    submit: "घटना रिपोर्ट प्रसारित करें",
    reporter: "रिपोर्टर का नाम",
    upvotes: "अपवोट्स",
    status_lbl: "सत्यापन स्थिति",
    gps_click: "जीपीएस निर्देशांक सेट करने के लिए मानचित्र पर क्लिक करें",
    cat_flood: "बाढ़ जलभराव",
    cat_landslide: "भूस्खलन / मलबा",
    cat_road: "मार्ग अवरोध",
    cat_power: "बिजली कटौती",
    cat_other: "अन्य खतरा",
    verify_btn: "रिपोर्ट सत्यापित करें",
    resolve_btn: "समाधान चिह्नित करें",
    success_msg: "घटना रिपोर्ट सफलतापूर्वक सबमिट की गई!",
    all_types: "सभी घटना श्रेणियां",
    all_status: "सभी स्थितियां",
    no_reports: "इस क्षेत्र में कोई घटना रिपोर्ट सक्रिय नहीं है।"
  },
  mr: {
    title: "नागरिक आपत्ती नोंदणी कक्ष",
    sub: "स्थानिक आपत्तींचे नकाशे तयार करा, बंद रस्ते व पाणी पातळीबद्दल घटना अहवाल द्या",
    map_telemetry: "जीआयएस आपत्ती अहवाल नकाशा",
    filters_title: "अहवाल शोध आणि फिल्टर",
    sub_btn: "नवीन घटना अहवाल द्या",
    type: "घटना प्रकार",
    details: "अहवाल तपशील",
    submit: "आपत्ती अहवाल पाठवा",
    reporter: "अहवालदाराचे नाव",
    upvotes: "अपव्होट्स",
    status_lbl: "सत्यापन स्थिती",
    gps_click: "लोकेशन निवडण्यासाठी नकाशावर क्लिक करा",
    cat_flood: "पूर / पाणी पातळी",
    cat_landslide: "दरड / मलबा",
    cat_road: "रस्ता बंद",
    cat_power: "वीज खंडित",
    cat_other: "इतर धोका",
    verify_btn: "सत्यापित करा",
    resolve_btn: "निवारण झाले",
    success_msg: "अहवाल यशस्वीरित्या पाठवला गेला!",
    all_types: "सर्व प्रकार",
    all_status: "सर्व स्थिती",
    no_reports: "या क्षेत्रात आपत्ती अहवाल सक्रिय नाहीत."
  }
};

interface Report {
  id: number;
  reporter_name: string;
  lat: number;
  lon: number;
  incident_type: string;
  details: string;
  upvotes: number;
  status: 'Unverified' | 'Verified' | 'Resolved' | 'Spam';
  created_at?: string;
}

export default function CommunityReports({ lang }: CommunityReportsProps) {
  const t = reportsTranslations[lang];
  const queryClient = useQueryClient();

  const [filterType, setFilterType] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  
  // Submit Form states
  const [formName, setFormName] = useState("");
  const [formType, setFormType] = useState("Flood Inundation");
  const [formLat, setFormLat] = useState(19.076);
  const [formLon, setFormLon] = useState(72.877);
  const [formDetails, setFormDetails] = useState("");
  const [success, setSuccess] = useState(false);

  const mapRef = useRef<L.Map | null>(null);
  const markersGroupRef = useRef<L.FeatureGroup | null>(null);
  const tempMarkerRef = useRef<L.Marker | null>(null);

  // Fetch Reports
  const { data: reports = [], refetch } = useQuery<Report[]>({
    queryKey: ['communityReports'],
    queryFn: () => apiClient.get('/api/community/reports')
  });

  // Submit report mutation
  const submitMutation = useMutation({
    mutationFn: (newReport: any) => apiClient.post('/api/community/report', newReport),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communityReports'] });
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setShowSubmitModal(false);
        setFormName("");
        setFormDetails("");
      }, 2000);
    }
  });

  // Map Initializer
  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map('reports-gis-map', {
        center: [19.076, 72.877],
        zoom: 12,
        zoomControl: false
      });

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20
      }).addTo(mapRef.current);

      L.control.zoom({ position: 'bottomright' }).addTo(mapRef.current);

      markersGroupRef.current = L.featureGroup().addTo(mapRef.current);

      // Handle map clicks to set form coordinates
      mapRef.current.on('click', (e: L.LeafletMouseEvent) => {
        const { lat, lng } = e.latlng;
        setFormLat(parseFloat(lat.toFixed(5)));
        setFormLon(parseFloat(lng.toFixed(5)));
        
        // Add a temporary placement marker on map
        if (mapRef.current) {
          if (tempMarkerRef.current) {
            mapRef.current.removeLayer(tempMarkerRef.current);
          }
          
          const tempIcon = L.divIcon({
            className: 'custom-temp-icon',
            html: `<div style="background-color: #3b82f6; width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff;" class="animate-ping"></div>`,
            iconSize: [12, 12],
            iconAnchor: [6, 6]
          });
          
          tempMarkerRef.current = L.marker([lat, lng], { icon: tempIcon }).addTo(mapRef.current);
        }
      });
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Sync Markers when reports update or filters change
  useEffect(() => {
    if (!mapRef.current || !markersGroupRef.current) return;

    markersGroupRef.current.clearLayers();

    filteredReports.forEach((rep) => {
      const colorMap: Record<string, string> = {
        "Flood Inundation": "#3b82f6",
        "Landslide / Debris": "#f97316",
        "Road Blockage": "#ef4444",
        "Power Outage": "#f59e0b"
      };
      
      const pinColor = colorMap[rep.incident_type] || "#a855f7";

      const pinIcon = L.divIcon({
        className: 'custom-incident-pin',
        html: `<div style="background-color: ${pinColor}; width: 14px; height: 14px; border-radius: 50%; border: 3px solid #fff; box-shadow: 0 0 10px ${pinColor};"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      });

      const popupHtml = `
        <div style="font-family: sans-serif; font-size: 11px; padding: 3px;">
          <h4 style="margin: 0 0 4px 0; font-weight: bold; color: ${pinColor}; uppercase">${rep.incident_type}</h4>
          <p style="margin: 0 0 6px 0; color: #cbd5e1;">${rep.details}</p>
          <span style="display: block; font-size: 9px; color: #94a3b8;">Reporter: <b>${rep.reporter_name}</b></span>
          <span style="display: block; font-size: 9px; color: #94a3b8; margin-top: 1px;">Status: <b>${rep.status}</b></span>
        </div>
      `;

      const m = L.marker([rep.lat, rep.lon], { icon: pinIcon })
        .bindPopup(popupHtml)
        .addTo(markersGroupRef.current!);
    });

    // Zoom map fit if there are markers
    if (filteredReports.length > 0 && markersGroupRef.current.getLayers().length > 0) {
      const bounds = markersGroupRef.current.getBounds();
      mapRef.current.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [reports, filterType, filterStatus, searchQuery]);

  const handleUpvote = (id: number) => {
    // Perform local optimistic upvote update
    queryClient.setQueryData(['communityReports'], (old: Report[] = []) => 
      old.map(r => r.id === id ? { ...r, upvotes: r.upvotes + 1 } : r)
    );
  };

  const handleStatusUpdate = (id: number, nextStatus: 'Verified' | 'Resolved' | 'Spam') => {
    queryClient.setQueryData(['communityReports'], (old: Report[] = []) => 
      old.map(r => r.id === id ? { ...r, status: nextStatus } : r)
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitMutation.mutate({
      reporter_name: formName || "Anonymous Citizen",
      incident_type: formType,
      lat: formLat,
      lon: formLon,
      details: formDetails
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Verified':
        return <span className="bg-blue-500/15 text-blue-400 border border-blue-500/35 px-2 py-0.5 rounded text-[8px] font-black uppercase">Verified</span>;
      case 'Resolved':
        return <span className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/35 px-2 py-0.5 rounded text-[8px] font-black uppercase">Resolved</span>;
      case 'Spam':
        return <span className="bg-slate-800 text-slate-500 px-2 py-0.5 rounded text-[8px] font-black uppercase">Spam</span>;
      default:
        return <span className="bg-amber-500/15 text-amber-400 border border-amber-500/35 px-2 py-0.5 rounded text-[8px] font-black uppercase animate-pulse">Unverified</span>;
    }
  };

  const filteredReports = reports.filter((rep) => {
    const matchesSearch = rep.details.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          rep.reporter_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === "all" || rep.incident_type === filterType;
    const matchesStatus = filterStatus === "all" || rep.status === filterStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="space-y-6">
      
      {/* Header Info Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-borderDim flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-full satellite-scanner pointer-events-none"></div>
        <div>
          <h2 className="text-lg font-bold text-textMain flex items-center gap-2">
            <ShieldAlert className="text-blue-500 w-5 h-5 shrink-0" />
            {t.title}
          </h2>
          <p className="text-xs text-textMuted mt-1">{t.sub}</p>
        </div>
        
        <button
          onClick={() => setShowSubmitModal(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 px-6 rounded-xl text-xs flex items-center gap-2 glow-button shrink-0"
        >
          <PlusCircle className="w-4 h-4" />
          {t.sub_btn}
        </button>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Interactive Map */}
        <div className="lg:col-span-2 flex flex-col h-[520px] glass-panel p-4 rounded-2xl border border-borderDim relative">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5 font-mono">
              <Compass className="w-4 h-4 text-blue-500" />
              {t.map_telemetry}
            </span>
          </div>
          
          <div id="reports-gis-map" className="flex-1 w-full rounded-xl border border-slate-950 z-10" />
        </div>

        {/* Right Search/Filter Sidebar & List */}
        <div className="space-y-4 flex flex-col h-[520px] overflow-hidden">
          
          {/* Filters Deck */}
          <div className="glass-panel p-4 rounded-xl border border-borderDim space-y-3 shrink-0">
            <h3 className="text-xs font-bold text-textMain uppercase tracking-wide flex items-center gap-1.5">
              <Sliders className="w-4 h-4 text-blue-500" />
              {t.filters_title}
            </h3>

            <div className="relative text-xs">
              <Search className="absolute left-2.5 top-2 text-slate-500 w-3.5 h-3.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search description or reporter..."
                className="w-full bg-slate-950 border border-borderDim px-8 py-1.5 rounded-lg text-textMain focus:outline-none font-semibold"
              />
            </div>

            <div className="grid grid-cols-2 gap-2 text-[10px] font-bold">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="bg-slate-950 border border-borderDim px-2.5 py-1.5 rounded-lg text-slate-400 focus:outline-none"
              >
                <option value="all">{t.all_types}</option>
                <option value="Flood Inundation">{t.cat_flood}</option>
                <option value="Landslide / Debris">{t.cat_landslide}</option>
                <option value="Road Blockage">{t.cat_road}</option>
                <option value="Power Outage">{t.cat_power}</option>
              </select>

              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="bg-slate-950 border border-borderDim px-2.5 py-1.5 rounded-lg text-slate-400 focus:outline-none"
              >
                <option value="all">{t.all_status}</option>
                <option value="Unverified">Unverified</option>
                <option value="Verified">Verified</option>
                <option value="Resolved">Resolved</option>
                <option value="Spam">Spam</option>
              </select>
            </div>
          </div>

          {/* Incident Reports List */}
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-1">
            {filteredReports.length > 0 ? (
              filteredReports.map((rep) => (
                <div key={rep.id} className="glass-panel p-4 rounded-xl border border-borderDim space-y-3 transition-all hover:bg-slate-900/25">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] font-extrabold uppercase text-gray-200 block">{rep.incident_type}</span>
                      <span className="text-[9px] text-slate-500 font-mono">GPS: {rep.lat.toFixed(4)}, {rep.lon.toFixed(4)}</span>
                    </div>
                    {getStatusBadge(rep.status)}
                  </div>
                  
                  <p className="text-xs text-textMuted leading-relaxed font-semibold">
                    {rep.details}
                  </p>

                  <div className="border-t border-borderDim/50 pt-2.5 flex items-center justify-between gap-4 text-[10px] font-bold">
                    <span className="text-slate-500">Reporter: <b className="text-slate-400 font-bold">{rep.reporter_name}</b></span>
                    
                    <div className="flex gap-2">
                      {/* Upvote */}
                      <button
                        onClick={() => handleUpvote(rep.id)}
                        className="bg-slate-950 hover:bg-slate-900 border border-borderDim px-2 py-1 rounded flex items-center gap-1.5 text-slate-400 hover:text-blue-400 transition-all font-bold cursor-pointer"
                      >
                        <ThumbsUp className="w-3.5 h-3.5" />
                        <span>{rep.upvotes}</span>
                      </button>

                      {/* EOC Controls for admin override verification */}
                      {rep.status === 'Unverified' && (
                        <button
                          onClick={() => handleStatusUpdate(rep.id, 'Verified')}
                          className="bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-1 rounded text-[8px] transition-all cursor-pointer font-black uppercase"
                        >
                          Verify
                        </button>
                      )}
                      
                      {rep.status === 'Verified' && (
                        <button
                          onClick={() => handleStatusUpdate(rep.id, 'Resolved')}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white px-2.5 py-1 rounded text-[8px] transition-all cursor-pointer font-black uppercase"
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="glass-panel py-16 rounded-xl border border-borderDim text-center text-slate-600 text-xs font-semibold">
                {t.no_reports}
              </div>
            )}
          </div>

        </div>

      </div>

      {/* Geotag Submission Modal Dialog */}
      {showSubmitModal && (
        <div className="fixed inset-0 bg-[#050811]/70 backdrop-blur-sm z-[2000] flex justify-center items-center p-4">
          <div className="w-full max-w-lg glass-panel-glow border border-blue-500/25 p-6 rounded-2xl space-y-4 animate-in fade-in zoom-in duration-200">
            
            <div className="flex justify-between items-center border-b border-slate-900 pb-3">
              <h3 className="text-sm font-bold text-textMain uppercase tracking-wide flex items-center gap-1.5">
                <MapPin className="text-blue-500 w-4.5 h-4.5" />
                {t.sub_btn}
              </h3>
              <button 
                onClick={() => setShowSubmitModal(false)}
                className="text-slate-400 hover:text-gray-200 p-1 hover:bg-slate-900 rounded transition-all"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {success ? (
              <div className="bg-emerald-950/40 border border-emerald-900 text-emerald-400 p-4 rounded-xl text-center text-xs font-bold animate-pulse">
                ✅ {t.success_msg}
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4 text-xs font-semibold">
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-textMuted">{t.reporter}</label>
                    <input
                      type="text" required value={formName} onChange={(e) => setFormName(e.target.value)}
                      placeholder="e.g. John Doe"
                      className="w-full bg-slate-950 border border-borderDim px-3.5 py-2 rounded-lg text-textMain focus:outline-none"
                    />
                  </div>
                  
                  <div className="space-y-1">
                    <label className="text-textMuted">{t.type}</label>
                    <select
                      value={formType} onChange={(e) => setFormType(e.target.value)}
                      className="w-full bg-slate-950 border border-borderDim px-3.5 py-2 rounded-lg text-textMain focus:outline-none"
                    >
                      <option value="Flood Inundation">{t.cat_flood}</option>
                      <option value="Landslide / Debris">{t.cat_landslide}</option>
                      <option value="Road Blockage">{t.cat_road}</option>
                      <option value="Power Outage">{t.cat_power}</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-textMuted">Latitude</label>
                    <input
                      type="number" step="0.00001" required value={formLat} onChange={(e) => setFormLat(parseFloat(e.target.value))}
                      className="w-full bg-slate-950 border border-borderDim px-3.5 py-2 rounded-lg text-textMain focus:outline-none font-mono"
                    />
                  </div>
                  
                  <div className="space-y-1">
                    <label className="text-textMuted">Longitude</label>
                    <input
                      type="number" step="0.00001" required value={formLon} onChange={(e) => setFormLon(parseFloat(e.target.value))}
                      className="w-full bg-slate-950 border border-borderDim px-3.5 py-2 rounded-lg text-textMain focus:outline-none font-mono"
                    />
                  </div>
                </div>

                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-borderDim/30 text-[10px] text-blue-400 text-center font-bold">
                  💡 {t.gps_click}
                </div>

                <div className="space-y-1">
                  <label className="text-textMuted">{t.details}</label>
                  <textarea
                    rows={3} required value={formDetails} onChange={(e) => setFormDetails(e.target.value)}
                    placeholder="Describe specific blockage details, flood water levels, power lines down, etc..."
                    className="w-full bg-slate-950 border border-borderDim px-3.5 py-2 rounded-lg text-textMain focus:outline-none font-medium text-xs leading-relaxed"
                  />
                </div>

                <button
                  type="submit" disabled={submitMutation.isPending}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 px-4 rounded-xl flex items-center justify-center gap-1.5 glow-button transition-all disabled:opacity-50"
                >
                  {t.submit}
                </button>

              </form>
            )}

          </div>
        </div>
      )}

    </div>
  );
}
