import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

interface AOIDrawerProps {
  mapInstance: L.Map | null;
  onAOIDrawn: (bounds: { min_lat: number, max_lat: number, min_lon: number, max_lon: number }) => void;
  isActive: boolean;
}

const AOIDrawer: React.FC<AOIDrawerProps> = ({ mapInstance, onAOIDrawn, isActive }) => {
  const layerRef = useRef<L.Rectangle | null>(null);
  const drawingRef = useRef<boolean>(false);
  const startPointRef = useRef<L.LatLng | null>(null);

  useEffect(() => {
    if (!mapInstance || !isActive) {
      if (layerRef.current && mapInstance) {
        mapInstance.removeLayer(layerRef.current);
        layerRef.current = null;
      }
      if (mapInstance) {
        mapInstance.getContainer().style.cursor = '';
        mapInstance.dragging.enable();
      }
      return;
    }

    mapInstance.getContainer().style.cursor = 'crosshair';
    mapInstance.dragging.disable();

    const onMouseDown = (e: L.LeafletMouseEvent) => {
      drawingRef.current = true;
      startPointRef.current = e.latlng;
      
      if (layerRef.current) {
        mapInstance.removeLayer(layerRef.current);
      }
      
      const bounds = L.latLngBounds(e.latlng, e.latlng);
      layerRef.current = L.rectangle(bounds, { color: '#00BFFF', weight: 2, fillOpacity: 0.2 }).addTo(mapInstance);
    };

    const onMouseMove = (e: L.LeafletMouseEvent) => {
      if (!drawingRef.current || !startPointRef.current || !layerRef.current) return;
      const bounds = L.latLngBounds(startPointRef.current, e.latlng);
      layerRef.current.setBounds(bounds);
    };

    const onMouseUp = (e: L.LeafletMouseEvent) => {
      if (!drawingRef.current || !startPointRef.current) return;
      drawingRef.current = false;
      
      const bounds = L.latLngBounds(startPointRef.current, e.latlng);
      if (layerRef.current) {
        layerRef.current.setBounds(bounds);
      }

      onAOIDrawn({
        min_lat: bounds.getSouth(),
        max_lat: bounds.getNorth(),
        min_lon: bounds.getWest(),
        max_lon: bounds.getEast()
      });
      
      // Optionally re-enable dragging after drawing
      // mapInstance.dragging.enable();
      // mapInstance.getContainer().style.cursor = '';
    };

    mapInstance.on('mousedown', onMouseDown);
    mapInstance.on('mousemove', onMouseMove);
    mapInstance.on('mouseup', onMouseUp);

    return () => {
      mapInstance.off('mousedown', onMouseDown);
      mapInstance.off('mousemove', onMouseMove);
      mapInstance.off('mouseup', onMouseUp);
      if (layerRef.current) {
         mapInstance.removeLayer(layerRef.current);
      }
      mapInstance.dragging.enable();
      mapInstance.getContainer().style.cursor = '';
    };
  }, [mapInstance, isActive, onAOIDrawn]);

  return null;
};

export default AOIDrawer;
