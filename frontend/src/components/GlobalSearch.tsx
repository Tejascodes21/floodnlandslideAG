import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, MapPin, AlertTriangle, HeartHandshake, X, Loader2 } from 'lucide-react';
import { apiClient } from '../config';

interface GlobalSearchProps {
  lang: 'en' | 'hi' | 'mr';
  onLocationSelect: (lat: number, lon: number, name: string) => void;
  onNavigateTab: (tab: string) => void;
}

interface NominatimResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
}

interface SearchResult {
  id: string;
  category: 'location' | 'alert' | 'volunteer' | 'report';
  title: string;
  subtitle: string;
  metadata: any;
}

export default function GlobalSearch({ lang, onLocationSelect, onNavigateTab }: GlobalSearchProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Close search when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Keyboard shortcut Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Unified search: geocoding + live backend volunteers
  const executeSearch = useCallback(async (term: string) => {
    if (!term.trim() || term.trim().length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    const matches: SearchResult[] = [];

    try {
      // 1. Nominatim geocoding — India restricted, 5 results
      const geoUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(term)}&countrycodes=in&limit=5&addressdetails=0`;
      const geoRes = await fetch(geoUrl, { headers: { 'Accept-Language': 'en' } });
      const geoData: NominatimResult[] = await geoRes.json();

      geoData.forEach((loc) => {
        const shortName = loc.display_name.split(',').slice(0, 2).join(',').trim();
        matches.push({
          id: `loc-${loc.place_id}`,
          category: 'location',
          title: shortName,
          subtitle: `GPS: ${parseFloat(loc.lat).toFixed(4)}, ${parseFloat(loc.lon).toFixed(4)}`,
          metadata: { lat: parseFloat(loc.lat), lon: parseFloat(loc.lon), name: shortName }
        });
      });
    } catch { /* Nominatim offline — continue with other sources */ }

    try {
      // 2. Live volunteers from backend
      const vols: any[] = await apiClient.get('/api/volunteers');
      const lowerTerm = term.toLowerCase();
      vols.forEach((v: any) => {
        const nameMatch = v.full_name?.toLowerCase().includes(lowerTerm);
        const skillMatch = v.skills?.toLowerCase().includes(lowerTerm);
        if (nameMatch || skillMatch) {
          matches.push({
            id: `vol-${v.id}`,
            category: 'volunteer',
            title: v.full_name,
            subtitle: `Skills: ${v.skills} | ${v.active ? '🟢 Active' : '⚪ Offline'}`,
            metadata: v
          });
        }
      });
    } catch { /* backend offline — continue */ }

    try {
      // 3. Live prediction history from backend — match by location name
      const history: any[] = await apiClient.get('/api/predict/history?limit=20');
      const lowerTerm = term.toLowerCase();
      history.forEach((rec: any) => {
        if (rec.location_name?.toLowerCase().includes(lowerTerm)) {
          const severity = rec.flood_severity || 'Unknown';
          matches.push({
            id: `alert-${rec.id}`,
            category: 'alert',
            title: `${rec.location_name}`,
            subtitle: `Flood: ${(rec.flood_prob * 100).toFixed(0)}% | Landslide: ${(rec.landslide_prob * 100).toFixed(0)}% | Severity: ${severity}`,
            metadata: { lat: rec.lat, lon: rec.lon, area: rec.location_name }
          });
        }
      });
    } catch { /* history offline */ }

    setResults(matches.slice(0, 10));
    setLoading(false);
  }, []);

  // Debounced search execution (300ms)
  const handleQueryChange = (val: string) => {
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => executeSearch(val), 300);
  };

  const handleResultClick = (res: SearchResult) => {
    setIsOpen(false);
    setQuery("");
    setResults([]);

    if (res.category === 'location' || res.category === 'alert') {
      onLocationSelect(res.metadata.lat, res.metadata.lon, res.metadata.name || res.metadata.area);
      onNavigateTab('dashboard');
    } else if (res.category === 'volunteer') {
      onNavigateTab('volunteers');
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'location': return <MapPin className="w-4 h-4 text-emerald-400" />;
      case 'alert': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'volunteer': return <HeartHandshake className="w-4 h-4 text-blue-400" />;
      default: return <Search className="w-4 h-4 text-slate-400" />;
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'location': return 'Location';
      case 'alert': return 'Prediction';
      case 'volunteer': return 'Volunteer';
      default: return '';
    }
  };

  return (
    <div ref={searchRef} className="relative z-50">
      {/* Search Input Bubble */}
      <div
        onClick={() => setIsOpen(true)}
        className="w-72 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 px-3.5 py-1.5 rounded-xl text-xs text-slate-400 flex items-center justify-between cursor-pointer transition-all gap-2"
      >
        <div className="flex items-center gap-2">
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <span>Quick console search...</span>
        </div>
        <kbd className="hidden sm:inline-block bg-slate-950 px-1.5 py-0.5 border border-slate-800 rounded text-[9px] text-slate-500 font-mono">
          Ctrl K
        </kbd>
      </div>

      {/* Expanded Search Command Palette */}
      {isOpen && (
        <div className="absolute top-10 left-0 w-96 glass-panel-glow border border-blue-500/20 rounded-xl overflow-hidden shadow-2xl flex flex-col p-1.5 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center gap-2 px-3 py-2 bg-slate-950/40 rounded-lg border border-slate-900 mb-1.5">
            {loading
              ? <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
              : <Search className="w-4 h-4 text-blue-400" />
            }
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => handleQueryChange(e.target.value)}
              placeholder="Search locations, volunteers, or past predictions..."
              className="flex-1 bg-transparent border-none text-xs text-gray-200 focus:outline-none placeholder-slate-500"
            />
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-gray-200 p-0.5 hover:bg-slate-900 rounded"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="max-h-72 overflow-y-auto px-1 py-0.5 space-y-1">
            {results.length > 0 ? (
              results.map((res) => (
                <div
                  key={res.id}
                  onClick={() => handleResultClick(res)}
                  className="flex items-start gap-3 p-2 bg-slate-950/20 hover:bg-blue-600/10 rounded-lg border border-transparent hover:border-blue-500/20 cursor-pointer transition-all group"
                >
                  <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 shrink-0">
                    {getCategoryIcon(res.category)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-gray-200 block truncate">{res.title}</span>
                      <span className="text-[8px] uppercase tracking-wider font-black text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded shrink-0">
                        {getCategoryLabel(res.category)}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 block truncate leading-relaxed">{res.subtitle}</span>
                  </div>
                </div>
              ))
            ) : query.trim() && !loading ? (
              <div className="text-center py-6 text-slate-500 text-[11px] font-medium leading-relaxed">
                No matching records found for "{query}"
              </div>
            ) : !query.trim() ? (
              <div className="py-4 px-2 space-y-1.5">
                <span className="text-[9px] font-black text-slate-500 tracking-wider uppercase block mb-1">EOC Quick Jumps:</span>
                <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                  <button
                    onClick={() => { setIsOpen(false); onNavigateTab('dashboard'); }}
                    className="bg-slate-950/40 hover:bg-slate-950 border border-slate-900 p-2 rounded-lg text-left text-slate-400 hover:text-gray-200 font-semibold"
                  >
                    📊 Overview Deck
                  </button>
                  <button
                    onClick={() => { setIsOpen(false); onNavigateTab('satellite'); }}
                    className="bg-slate-950/40 hover:bg-slate-950 border border-slate-900 p-2 rounded-lg text-left text-slate-400 hover:text-gray-200 font-semibold"
                  >
                    🗺️ GIS Workstation
                  </button>
                  <button
                    onClick={() => { setIsOpen(false); onNavigateTab('volunteers'); }}
                    className="bg-slate-950/40 hover:bg-slate-950 border border-slate-900 p-2 rounded-lg text-left text-slate-400 hover:text-gray-200 font-semibold"
                  >
                    👷 Volunteer Hub
                  </button>
                  <button
                    onClick={() => { setIsOpen(false); onNavigateTab('sos'); }}
                    className="bg-slate-950/40 hover:bg-slate-950 border border-slate-900 p-2 rounded-lg text-left text-slate-400 hover:text-gray-200 font-semibold"
                  >
                    🚨 SOS Distress
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
