import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

interface EvacuationRouterProps {
  mapInstance: L.Map | null;
  routeData: any; // Data from /gis/route
  visible: boolean;
}

const EvacuationRouter: React.FC<EvacuationRouterProps> = ({ mapInstance, routeData, visible }) => {
  const layerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapInstance || !routeData || !visible) {
      if (layerRef.current && mapInstance) {
        layerRef.current.clearLayers();
        mapInstance.removeLayer(layerRef.current);
      }
      return;
    }

    if (!layerRef.current) {
      layerRef.current = L.layerGroup();
    } else {
      layerRef.current.clearLayers();
    }

    const { route_points, safe_shelters } = routeData;

    // Draw route polyline
    if (route_points && route_points.length > 0) {
      const latlngs = route_points.map((p: any) => [p.lat, p.lon] as [number, number]);
      const polyline = L.polyline(latlngs, {
        color: '#00FA9A', // MediumSpringGreen for safe route
        weight: 5,
        opacity: 0.8,
        dashArray: '10, 10' // Dashed line to indicate planned route
      });
      polyline.addTo(layerRef.current);

      // Start marker
      L.circleMarker(latlngs[0], {
        radius: 6, fillColor: '#ff0000', color: '#fff', weight: 2, fillOpacity: 1
      }).bindTooltip("Evacuation Start").addTo(layerRef.current);

      // End marker
      L.circleMarker(latlngs[latlngs.length - 1], {
        radius: 8, fillColor: '#00FA9A', color: '#fff', weight: 2, fillOpacity: 1
      }).bindTooltip("Destination").addTo(layerRef.current);
    }

    // Draw shelters
    if (safe_shelters && safe_shelters.length > 0) {
      safe_shelters.forEach((shelter: any) => {
        const iconHtml = `<div style="background-color:#4169E1; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid white; color:white; font-weight:bold;">S</div>`;
        const shelterIcon = L.divIcon({ html: iconHtml, className: 'custom-shelter-icon', iconSize: [24, 24] });
        
        L.marker([shelter.lat, shelter.lon], { icon: shelterIcon })
          .bindTooltip(`<b>${shelter.name}</b><br/>Capacity: ${shelter.capacity}`)
          .addTo(layerRef.current!);
      });
    }

    layerRef.current.addTo(mapInstance);

    // Optional: fit bounds
    if (route_points && route_points.length > 0) {
      const bounds = L.latLngBounds(route_points.map((p: any) => [p.lat, p.lon]));
      mapInstance.fitBounds(bounds, { padding: [50, 50] });
    }

    return () => {
      if (layerRef.current && mapInstance) {
        layerRef.current.clearLayers();
        mapInstance.removeLayer(layerRef.current);
      }
    };
  }, [mapInstance, routeData, visible]);

  return null; // pure map overlay component
};

export default EvacuationRouter;
