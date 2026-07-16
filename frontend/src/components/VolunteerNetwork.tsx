import React, { useState, useEffect, useRef } from "react";
import {
  HeartHandshake,
  Compass,
  Navigation,
  Search,
  Sliders,
  ShieldAlert,
  CheckCircle,
  Car,
  LifeBuoy,
  Users,
  Activity,
  Plus,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import L from "leaflet";
import { apiClient } from "../config";

interface VolunteerNetworkProps {
  lang: "en" | "hi" | "mr";
}

const volunteerTranslations = {
  en: {
    title: "Volunteer dispatch Control Board",
    sub: "Coordinate NGO rescue logistics, monitor volunteer standby networks, and dispatch powerboat vectors",
    map_lbl: "Standby Volunteer GIS Map",
    kpi_standby: "Standby Rescuers",
    kpi_active: "Active Missions",
    kpi_sos: "Distress Signals",
    vols_list: "Volunteer Registry",
    missions_list: "Active Emergency Assignments",
    search_lbl: "Search by name or skills...",
    skills: "Critical Skills",
    vehicle: "Vehicle Type",
    status: "Availability Status",
    dispatch_btn: "Dispatch Rescuer",
    complete_btn: "Mark Completed",
    col_vol: "Rescuer",
    col_citizen: "Citizen",
    col_type: "Emergency Type",
    col_status: "Mission Status",
    col_route: "Safe Route GPS",
    active: "Active Mission",
    standby: "Standby Ready",
    no_vols: "No volunteers matching criteria found.",
  },
  hi: {
    title: "स्वयंसेवक प्रेषण नियंत्रण बोर्ड",
    sub: "एनजीओ बचाव रसद का समन्वय करें, स्वयंसेवक नेटवर्क की निगरानी करें, और बचाव नौकाओं को तैनात करें",
    map_lbl: "स्वयंसेवक जीआईएस मानचित्र",
    kpi_standby: "तैयार स्वयंसेवक",
    kpi_active: "सक्रिय मिशन",
    kpi_sos: "संकट संकेत (SOS)",
    vols_list: "स्वयंसेवक रजिस्ट्री",
    missions_list: "सक्रिय आपातकालीन कार्य",
    search_lbl: "नाम या कौशल से खोजें...",
    skills: "महत्वपूर्ण कौशल",
    vehicle: "वाहन का प्रकार",
    status: "उपलब्धता स्थिति",
    dispatch_btn: "बचावकर्मी भेजें",
    complete_btn: "पूर्ण चिह्नित करें",
    col_vol: "बचावकर्मी",
    col_citizen: "नागरिक",
    col_type: "संकट प्रकार",
    col_status: "मिशन स्थिति",
    col_route: "जीपीएस मार्ग",
    active: "सक्रिय मिशन",
    standby: "तैयार (Standby)",
    no_vols: "कोई स्वयंसेवक नहीं मिला।",
  },
  mr: {
    title: "स्वयंसेवक मोहीम नियंत्रण फलक",
    sub: "मदत पथकांचे व्यवस्थापन करा, स्वयंसेवक संपर्क यंत्रणा नियंत्रित करा आणि बचाव नौका मार्ग निश्चित करा",
    map_lbl: "स्वयंसेवक भौगोलिक नकाशा",
    kpi_standby: "कार्यरत स्वयंसेवक",
    kpi_active: "सक्रिय मोहिमा",
    kpi_sos: "मदत संदेश (SOS)",
    vols_list: "स्वयंसेवक यादी",
    missions_list: "सक्रिय आपत्कालीन मोहिमा",
    search_lbl: "नाव किंवा कौशल्य तपासा...",
    skills: "महत्वाची कौशल्ये",
    vehicle: "वाहन प्रकार",
    status: "उपलब्धता स्थिती",
    dispatch_btn: "पथक रवाना करा",
    complete_btn: "मोहीम पूर्ण झाली",
    col_vol: "बचावकर्ते",
    col_citizen: "नागरिक",
    col_type: "धोका प्रकार",
    col_status: "मोहीम स्थिती",
    col_route: "सुरक्षित मार्ग GPS",
    active: "सक्रिय मोहीम",
    standby: "कार्यरत (Standby)",
    no_vols: "स्वयंसेवक आढळले नाहीत.",
  },
};

interface Volunteer {
  id: number;
  full_name: string;
  phone: string;
  lat: number;
  lon: number;
  vehicle_type: string;
  skills: string;
  active: boolean;
}

interface RescueMission {
  mission_id: number;
  volunteer_name: string;
  vehicle: string;
  citizen: string;
  emergency_type: string;
  route: { lat: number; lon: number }[];
  status: string;
}

export default function VolunteerNetwork({ lang }: VolunteerNetworkProps) {
  const t = volunteerTranslations[lang];
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState("");
  const [filterSkill, setFilterSkill] = useState("all");
  const [filterVehicle, setFilterVehicle] = useState("all");

  const mapRef = useRef<L.Map | null>(null);
  const volunteerGroupRef = useRef<L.FeatureGroup | null>(null);
  const routeGroupRef = useRef<L.FeatureGroup | null>(null);

  // Fetch Volunteers
  const { data: volunteers = [], refetch: refetchVols } = useQuery<Volunteer[]>(
    {
      queryKey: ["volunteers"],
      queryFn: () => apiClient.get("/api/volunteers"),
      refetchInterval: 12000, // Poll every 12s
    },
  );

  // Fetch Missions
  const { data: missions = [], refetch: refetchMissions } = useQuery<
    RescueMission[]
  >({
    queryKey: ["rescueMissions"],
    queryFn: async () => {
      try {
        return await apiClient.get("/api/missions");
      } catch (e) {
        // Fallback mock active missions if offline
        return [
          {
            mission_id: 201,
            volunteer_name: "Volunteer Captain",
            vehicle: "Inflatable Powerboat",
            citizen: "Sanjay Shah",
            emergency_type: "Flood Inundation Trapped",
            route: [
              { lat: 19.076, lon: 72.877 },
              { lat: 19.092, lon: 72.88 },
              { lat: 19.125, lon: 72.89 },
            ],
            status: "Assigned",
          },
        ];
      }
    },
    refetchInterval: 12000,
  });

  const dispatchMutation = useMutation({
    mutationFn: ({
      volunteerId,
      requestBody,
    }: {
      volunteerId: number;
      requestBody: any;
    }) => apiClient.post(`/api/volunteer/${volunteerId}/dispatch`, requestBody),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["volunteers"] });
      queryClient.invalidateQueries({ queryKey: ["rescueMissions"] });
    },
  });

  const completeMissionMutation = useMutation({
    mutationFn: (missionId: number) =>
      apiClient.post(`/api/mission/${missionId}/complete`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["volunteers"] });
      queryClient.invalidateQueries({ queryKey: ["rescueMissions"] });
    },
  });

  // Map Setup
  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map("volunteer-gis-map", {
        center: [19.076, 72.877],
        zoom: 12,
        zoomControl: false,
      });

      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        {
          maxZoom: 20,
        },
      ).addTo(mapRef.current);

      L.control.zoom({ position: "bottomright" }).addTo(mapRef.current);

      volunteerGroupRef.current = L.featureGroup().addTo(mapRef.current);
      routeGroupRef.current = L.featureGroup().addTo(mapRef.current);
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Sync Map Markers & Routes
  useEffect(() => {
    if (!mapRef.current || !volunteerGroupRef.current || !routeGroupRef.current)
      return;

    volunteerGroupRef.current.clearLayers();
    routeGroupRef.current.clearLayers();

    // Plot Volunteers
    filteredVolunteers.forEach((vol) => {
      const pinColor = vol.active ? "#3b82f6" : "#10b981"; // blue if busy, green if standby

      const volIcon = L.divIcon({
        className: "custom-vol-pin",
        html: `<div style="background-color: ${pinColor}; width: 12px; height: 12px; border-radius: 50%; border: 2.5px solid #fff; box-shadow: 0 0 8px ${pinColor};"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6],
      });

      const popupHtml = `
        <div style="font-family: sans-serif; font-size: 11px; padding: 2px;">
          <h4 style="margin: 0 0 3px 0; font-weight: bold; color: ${pinColor};">${vol.full_name}</h4>
          <span style="display: block; font-size: 9px; color: #cbd5e1;">Skills: ${vol.skills}</span>
          <span style="display: block; font-size: 9px; color: #cbd5e1; margin-top: 1px;">Vehicle: ${vol.vehicle_type}</span>
          <span style="display: block; font-size: 9px; font-weight: bold; color: ${vol.active ? "#60a5fa" : "#34d399"}; margin-top: 3px;">
            ${vol.active ? "DISPATCHED" : "STANDBY READY"}
          </span>
        </div>
      `;

      L.marker([vol.lat, vol.lon], { icon: volIcon })
        .bindPopup(popupHtml)
        .addTo(volunteerGroupRef.current!);
    });

    // Plot active mission routes
    missions.forEach((mission) => {
      if (mission.route && mission.route.length > 1) {
        const polyPoints = mission.route.map(
          (pt) => [pt.lat, pt.lon] as L.LatLngTuple,
        );
        L.polyline(polyPoints, {
          color: "#3b82f6",
          weight: 4,
          dashArray: "6, 6",
          opacity: 0.8,
        }).addTo(routeGroupRef.current!);
      }
    });

    // Zoom map fit if elements exist
    const hasVols = volunteerGroupRef.current.getLayers().length > 0;
    if (hasVols && mapRef.current) {
      const bounds = volunteerGroupRef.current.getBounds();
      mapRef.current.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [volunteers, missions, searchQuery, filterSkill, filterVehicle]);

  const handleUpdateMissionStatus = (id: number) => {
    completeMissionMutation.mutate(id, {
      onError: (err) => {
        console.error("Mission completion failed", err);
      },
    });
  };

  const handleTriggerDispatch = (volId: number) => {
    const vol = volunteers.find((v) => v.id === volId);
    if (!vol) return;

    const requestBody = {
      emergency_type: "Evacuation logistics",
      details: `Dispatch request from dashboard for ${vol.full_name}`,
      citizen_name: "Local Citizen",
      lat: vol.lat + 0.003,
      lon: vol.lon - 0.003,
    };

    dispatchMutation.mutate(
      { volunteerId: volId, requestBody },
      {
        onError: (err) => {
          console.error("Dispatch failed", err);
        },
      },
    );
  };

  const filteredVolunteers = volunteers.filter((vol) => {
    const matchesSearch =
      vol.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      vol.skills.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSkill =
      filterSkill === "all" ||
      vol.skills.toLowerCase().includes(filterSkill.toLowerCase());
    const matchesVehicle =
      filterVehicle === "all" ||
      vol.vehicle_type.toLowerCase().includes(filterVehicle.toLowerCase());
    return matchesSearch && matchesSkill && matchesVehicle;
  });

  const standbyCount = volunteers.filter((v) => !v.active).length;
  const activeMissionsCount = missions.filter(
    (m) => m.status !== "Completed" && m.status !== "Resolved",
  ).length;

  return (
    <div className="space-y-6">
      {/* Header Info Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-borderDim flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-full satellite-scanner pointer-events-none"></div>
        <div>
          <h2 className="text-lg font-bold text-textMain flex items-center gap-2">
            <HeartHandshake className="text-blue-500 w-5 h-5 shrink-0" />
            {t.title}
          </h2>
          <p className="text-xs text-textMuted mt-1">{t.sub}</p>
        </div>
      </div>

      {/* KPI indicators grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total standby */}
        <div className="glass-panel p-4 rounded-xl border border-borderDim flex items-center justify-between">
          <div>
            <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">
              {t.kpi_standby}
            </span>
            <span className="text-2xl font-black block mt-1 text-emerald-400">
              {standbyCount} standby
            </span>
          </div>
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg">
            <Users className="w-5 h-5" />
          </div>
        </div>

        {/* Total active missions */}
        <div className="glass-panel p-4 rounded-xl border border-borderDim flex items-center justify-between">
          <div>
            <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">
              {t.kpi_active}
            </span>
            <span className="text-2xl font-black block mt-1 text-blue-400">
              {activeMissionsCount} active
            </span>
          </div>
          <div className="p-3 bg-blue-500/10 border border-blue-500/30 text-blue-500 rounded-lg">
            <Navigation className="w-5 h-5 animate-pulse" />
          </div>
        </div>

        {/* System distress signals */}
        <div className="glass-panel p-4 rounded-xl border border-borderDim flex items-center justify-between">
          <div>
            <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">
              {t.kpi_sos}
            </span>
            <span className="text-2xl font-black block mt-1 text-red-500">
              2 Unresolved
            </span>
          </div>
          <div className="p-3 bg-red-500/10 border border-red-500/30 text-red-500 rounded-lg">
            <ShieldAlert className="w-5 h-5 pulse-threat" />
          </div>
        </div>
      </div>

      {/* Main Grid: Map vs Registry Side Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Map View */}
        <div className="lg:col-span-2 flex flex-col h-[520px] glass-panel p-4 rounded-2xl border border-borderDim relative">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5 font-mono">
              <Compass className="w-4 h-4 text-blue-500" />
              {t.map_lbl}
            </span>
          </div>

          <div
            id="volunteer-gis-map"
            className="flex-1 w-full rounded-xl border border-slate-950 z-10"
          />
        </div>

        {/* Right Search/Registry Sidebar */}
        <div className="space-y-4 flex flex-col h-[520px] overflow-hidden">
          {/* Filters */}
          <div className="glass-panel p-4 rounded-xl border border-borderDim space-y-3 shrink-0">
            <h3 className="text-xs font-bold text-textMain uppercase tracking-wide flex items-center gap-1.5">
              <Sliders className="w-4 h-4 text-blue-500" />
              {t.vols_list}
            </h3>

            <div className="relative text-xs">
              <Search className="absolute left-2.5 top-2 text-slate-500 w-3.5 h-3.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t.search_lbl}
                className="w-full bg-slate-950 border border-borderDim px-8 py-1.5 rounded-lg text-textMain focus:outline-none font-semibold"
              />
            </div>

            <div className="grid grid-cols-2 gap-2 text-[10px] font-bold">
              <select
                value={filterSkill}
                onChange={(e) => setFilterSkill(e.target.value)}
                className="bg-slate-950 border border-borderDim px-2 py-1.5 rounded-lg text-slate-400 focus:outline-none"
              >
                <option value="all">All Rescue Skills</option>
                <option value="first aid">First Aid</option>
                <option value="boat">Water / Boat Operator</option>
                <option value="paramedic">Paramedic</option>
                <option value="climber">Slope Climbing</option>
              </select>

              <select
                value={filterVehicle}
                onChange={(e) => setFilterVehicle(e.target.value)}
                className="bg-slate-950 border border-borderDim px-2 py-1.5 rounded-lg text-slate-400 focus:outline-none"
              >
                <option value="all">All Vehicle Assets</option>
                <option value="boat">Inflatable Boat</option>
                <option value="truck">4x4 Truck</option>
                <option value="ambulance">Emergency Ambulance</option>
                <option value="drone">Aerial Drone</option>
              </select>
            </div>
          </div>

          {/* Volunteer List Cards */}
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-1">
            {filteredVolunteers.length > 0 ? (
              filteredVolunteers.map((vol) => (
                <div
                  key={vol.id}
                  className="glass-panel p-4 rounded-xl border border-borderDim space-y-2.5 transition-all hover:bg-slate-900/25"
                >
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-gray-200 block">
                      {vol.full_name}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[8px] font-bold border uppercase tracking-wider ${
                        vol.active
                          ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                          : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      }`}
                    >
                      {vol.active ? t.active : t.standby}
                    </span>
                  </div>

                  <div className="text-[10px] font-semibold text-textMuted space-y-1">
                    <div>
                      {t.skills}:{" "}
                      <span className="text-slate-400">{vol.skills}</span>
                    </div>
                    <div>
                      {t.vehicle}:{" "}
                      <span className="text-slate-400">{vol.vehicle_type}</span>
                    </div>
                  </div>

                  {!vol.active && (
                    <button
                      onClick={() => handleTriggerDispatch(vol.id)}
                      className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black py-1 px-3 rounded text-[10px] transition-all cursor-pointer uppercase"
                    >
                      {t.dispatch_btn}
                    </button>
                  )}
                </div>
              ))
            ) : (
              <div className="glass-panel py-16 rounded-xl border border-borderDim text-center text-slate-600 text-xs font-semibold">
                {t.no_vols}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Active Rescue Missions Log Table */}
      {missions.length > 0 && (
        <div className="glass-panel p-5 rounded-2xl border border-borderDim space-y-4">
          <h3 className="text-xs font-bold text-textMain border-b border-slate-900 pb-3 uppercase tracking-wide flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-blue-500" />
            {t.missions_list}
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-semibold text-textMuted">
              <thead>
                <tr className="border-b border-borderDim text-[10px] text-slate-500 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Mission ID</th>
                  <th className="py-2.5 px-3">{t.col_vol}</th>
                  <th className="py-2.5 px-3">{t.col_citizen}</th>
                  <th className="py-2.5 px-3">{t.col_type}</th>
                  <th className="py-2.5 px-3">{t.col_route}</th>
                  <th className="py-2.5 px-3">{t.col_status}</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderDim/40">
                {missions.map((m) => (
                  <tr key={m.mission_id} className="hover:bg-slate-900/10">
                    <td className="py-3 px-3 font-mono font-bold text-slate-400">
                      #MS-{m.mission_id}
                    </td>
                    <td className="py-3 px-3 text-textMain">
                      {m.volunteer_name}{" "}
                      <span className="text-[10px] text-slate-500">
                        ({m.vehicle})
                      </span>
                    </td>
                    <td className="py-3 px-3 text-textMain">{m.citizen}</td>
                    <td className="py-3 px-3 text-red-400 font-bold">
                      {m.emergency_type}
                    </td>
                    <td className="py-3 px-3 font-mono text-[10px] text-blue-400">
                      {m.route
                        ? `(${m.route[0]?.lat.toFixed(3)}, ${m.route[0]?.lon.toFixed(3)}) -> (${m.route[m.route.length - 1]?.lat.toFixed(3)}, ${m.route[m.route.length - 1]?.lon.toFixed(3)})`
                        : "--"}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                          m.status === "Completed" || m.status === "Resolved"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse"
                        }`}
                      >
                        {m.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      {m.status !== "Completed" && m.status !== "Resolved" && (
                        <button
                          onClick={() =>
                            handleUpdateMissionStatus(m.mission_id, "Completed")
                          }
                          className="bg-emerald-600 hover:bg-emerald-500 text-white font-black py-1 px-3 rounded text-[9px] transition-all cursor-pointer uppercase"
                        >
                          {t.complete_btn}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
