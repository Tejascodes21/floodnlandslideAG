import React, { useState, useEffect, useRef } from 'react';
import { Bell, X, AlertTriangle, ShieldAlert, Info, Check } from 'lucide-react';
import { useRealTime, RealTimeAlert } from '../hooks/useRealTime';

interface NotificationCenterProps {
  lang: 'en' | 'hi' | 'mr';
  onNotificationSelect: (lat: number, lon: number, name: string) => void;
}

export default function NotificationCenter({ lang, onNotificationSelect }: NotificationCenterProps) {
  const { alerts: wsAlerts, isConnected } = useRealTime();
  const [isOpen, setIsOpen] = useState(false);
  const [localNotifications, setLocalNotifications] = useState<RealTimeAlert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filterSeverity, setFilterSeverity] = useState<'all' | 'extreme' | 'high' | 'moderate'>('all');
  
  const containerRef = useRef<HTMLDivElement>(null);

  // Sync WebSocket alerts
  useEffect(() => {
    if (wsAlerts.length > 0) {
      setLocalNotifications(wsAlerts);
      setUnreadCount(wsAlerts.length);
    }
  }, [wsAlerts]);

  // Initial seed if no websocket alerts are active
  useEffect(() => {
    if (localNotifications.length === 0) {
      const seedAlerts: RealTimeAlert[] = [
        {
          id: "alert-1",
          location_name: "Western Ghats, Maharashtra",
          lat: 19.076,
          lon: 72.877,
          message: "Monsoon depression detected: Heavy landslide susceptibility warning in hillsides.",
          severity: "high",
          timestamp: new Date().toISOString()
        },
        {
          id: "alert-2",
          location_name: "Mithi River Basin",
          lat: 19.080,
          lon: 72.870,
          message: "Hydro Gauge Warning: Water level exceeding critical warning boundary.",
          severity: "extreme",
          timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString()
        },
        {
          id: "alert-3",
          location_name: "Lonavala Hill Station",
          lat: 18.734,
          lon: 73.407,
          message: "Landslide susceptibility index elevated to 89% saturation.",
          severity: "extreme",
          timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString()
        }
      ];
      setLocalNotifications(seedAlerts);
      setUnreadCount(3);
    }
  }, []);

  // Listen to the window event for custom toast events
  useEffect(() => {
    const handleAlertToast = (e: Event) => {
      const customEvent = e as CustomEvent<RealTimeAlert>;
      const newAlert = customEvent.detail;
      setLocalNotifications(prev => {
        const filtered = prev.filter(n => n.id !== newAlert.id);
        return [newAlert, ...filtered];
      });
      setUnreadCount(c => c + 1);
    };

    window.addEventListener('eoc-alert-toast', handleAlertToast);
    return () => window.removeEventListener('eoc-alert-toast', handleAlertToast);
  }, []);

  // Close popup on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setUnreadCount(0); // Mark all as read when opening
    }
  };

  const handleClearAll = () => {
    setLocalNotifications([]);
    setUnreadCount(0);
  };

  const handleNotificationClick = (n: RealTimeAlert) => {
    if (n.lat && n.lon) {
      onNotificationSelect(n.lat, n.lon, n.location_name || "Alert sector");
      setIsOpen(false);
    }
  };

  const getAlertIcon = (severity?: string) => {
    switch (severity) {
      case 'extreme': return <ShieldAlert className="w-4 h-4 text-red-500 animate-bounce" />;
      case 'high': return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'moderate': return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      default: return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const getAlertBorder = (severity?: string) => {
    switch (severity) {
      case 'extreme': return 'border-l-4 border-l-red-500 bg-red-950/10 border-slate-900';
      case 'high': return 'border-l-4 border-l-orange-500 bg-orange-950/5 border-slate-900';
      case 'moderate': return 'border-l-4 border-l-amber-500 bg-amber-950/5 border-slate-900';
      default: return 'border-l-4 border-l-blue-500 bg-slate-950/40 border-slate-900';
    }
  };

  const filteredNotifications = localNotifications.filter(n => {
    if (filterSeverity === 'all') return true;
    return n.severity === filterSeverity;
  });

  return (
    <div ref={containerRef} className="relative z-50">
      {/* Trigger Bell Icon */}
      <button 
        onClick={handleToggle}
        className="relative p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-slate-400 hover:text-gray-200 transition-all flex items-center justify-center cursor-pointer"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[16px] h-4 rounded-full bg-red-600 text-white font-extrabold text-[8px] flex items-center justify-center px-1 animate-pulse">
            {unreadCount}
          </span>
        )}
      </button>

      {/* Popover Pane */}
      {isOpen && (
        <div className="absolute top-10 right-0 w-80 glass-panel-glow border border-blue-500/20 rounded-xl overflow-hidden shadow-2xl flex flex-col p-1.5 animate-in fade-in slide-in-from-top-2 duration-200">
          
          {/* Header */}
          <div className="flex justify-between items-center px-3 py-2 bg-slate-950/40 border border-slate-900 rounded-lg mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-gray-200 uppercase tracking-wide">EOC Broadcasts</span>
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-amber-500'} animate-pulse`} title={isConnected ? "WebSocket Live" : "WebSocket Connecting"} />
            </div>
            <div className="flex gap-2">
              <button 
                onClick={handleClearAll}
                className="text-[9px] font-black uppercase text-slate-500 hover:text-slate-300 transition-all"
              >
                Clear All
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex gap-1 mb-2 px-1 text-[9px]">
            {(['all', 'extreme', 'high', 'moderate'] as const).map(sev => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-2 py-0.5 rounded capitalize font-bold border transition-all ${filterSeverity === sev ? 'bg-blue-600/25 border-blue-500/40 text-blue-300' : 'bg-slate-950/40 border-transparent text-slate-500 hover:text-slate-300'}`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Alerts List */}
          <div className="max-h-64 overflow-y-auto px-1 space-y-1">
            {filteredNotifications.length > 0 ? (
              filteredNotifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => handleNotificationClick(n)}
                  className={`p-2.5 rounded-lg border flex gap-2.5 cursor-pointer transition-all ${getAlertBorder(n.severity)} hover:bg-slate-900/60`}
                >
                  <div className="shrink-0 pt-0.5">
                    {getAlertIcon(n.severity)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-baseline gap-1 mb-0.5">
                      <span className="text-[10px] font-black uppercase text-gray-200 tracking-wider truncate">{n.location_name}</span>
                      <span className="text-[8px] text-slate-500 font-mono shrink-0">
                        {n.timestamp ? new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'now'}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 font-medium leading-relaxed">
                      {n.message}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-500 text-[11px] font-medium">
                No active broadcasts. Grid secure.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
