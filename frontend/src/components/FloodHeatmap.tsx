import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface FloodHeatmapProps {
  mapInstance: L.Map | null;
  heatmapData: any; // Data from /predict/heatmap endpoint
  visible: boolean;
  opacity?: number;
}

const FloodHeatmap: React.FC<FloodHeatmapProps> = ({ mapInstance, heatmapData, visible, opacity = 0.6 }) => {
  const layerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapInstance || !heatmapData || !visible) {
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

    const { cells } = heatmapData;

    cells.forEach((cell: any) => {
      const { lat, lon, bounds, flood_risk } = cell;
      
      // Determine color based on risk
      let color = '#00ff00';
      if (flood_risk > 0.75) color = '#ff0000';
      else if (flood_risk > 0.5) color = '#ff8800';
      else if (flood_risk > 0.25) color = '#ffff00';

      const rectBounds = [
        [bounds.min_lat, bounds.min_lon],
        [bounds.max_lat, bounds.max_lon]
      ] as L.LatLngBoundsExpression;

      const rect = L.rectangle(rectBounds, {
        color: color,
        weight: 0,
        fillColor: color,
        fillOpacity: opacity * flood_risk // Higher risk = slightly more opaque
      });

      rect.bindTooltip(`Flood Risk: ${(flood_risk * 100).toFixed(1)}%`);
      
      if (layerRef.current) {
        rect.addTo(layerRef.current);
      }
    });

    if (layerRef.current) {
      layerRef.current.addTo(mapInstance);
    }

    return () => {
      if (layerRef.current && mapInstance) {
        layerRef.current.clearLayers();
        mapInstance.removeLayer(layerRef.current);
      }
    };
  }, [mapInstance, heatmapData, visible, opacity]);

  return null; // This is a logic component, no DOM elements
};

export default FloodHeatmap;
