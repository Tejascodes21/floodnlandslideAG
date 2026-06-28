import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface LandslideOverlayProps {
  mapInstance: L.Map | null;
  heatmapData: any; // Data from /predict/heatmap endpoint
  visible: boolean;
  opacity?: number;
}

const LandslideOverlay: React.FC<LandslideOverlayProps> = ({ mapInstance, heatmapData, visible, opacity = 0.6 }) => {
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
      const { bounds, landslide_risk, slope } = cell;
      
      // Skip very low risk to reduce clutter
      if (landslide_risk < 0.2) return;

      let color = '#8B4513'; // SaddleBrown
      if (landslide_risk > 0.8) color = '#800000'; // Maroon
      else if (landslide_risk > 0.5) color = '#A0522D'; // Sienna

      const rectBounds = [
        [bounds.min_lat, bounds.min_lon],
        [bounds.max_lat, bounds.max_lon]
      ] as L.LatLngBoundsExpression;

      const rect = L.rectangle(rectBounds, {
        color: color,
        weight: 1,
        fillColor: color,
        fillOpacity: opacity * landslide_risk
      });

      rect.bindTooltip(`Landslide Risk: ${(landslide_risk * 100).toFixed(1)}%<br/>Slope: ${slope}°`);
      
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

  return null;
};

export default LandslideOverlay;
