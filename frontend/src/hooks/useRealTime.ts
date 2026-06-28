import { useEffect, useState, useRef } from 'react';
import { API_BASE_URL } from '../config';

export interface RealTimeAlert {
  id?: string;
  location_name?: string;
  lat?: number;
  lon?: number;
  message?: string;
  severity?: 'low' | 'moderate' | 'high' | 'extreme' | 'none';
  timestamp?: string;
}

export function useRealTime() {
  const [alerts, setAlerts] = useState<RealTimeAlert[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = () => {
    // Convert HTTP base URL to WS protocol
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = '';
    
    if (API_BASE_URL.startsWith('http')) {
      wsUrl = API_BASE_URL.replace(/^http(s)?:\/\//, `${wsProto}//`) + '/api/realtime/ws';
    } else {
      // Relative URL fallback
      const host = window.location.host;
      wsUrl = `${wsProto}//${host}/api/realtime/ws`;
    }

    try {
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        console.log('EOC WebSockets connection established');
      };

      socket.onclose = () => {
        setIsConnected(false);
        console.log('EOC WebSockets connection closed. Attempting reconnect...');
        scheduleReconnect();
      };

      socket.onerror = (error) => {
        console.error('EOC WebSockets connection error:', error);
        socket.close();
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          
          if (payload.type === 'init' && payload.alerts) {
            // Initial cached alerts list
            setAlerts(payload.alerts);
          } else if (payload.type === 'alert' && payload.data) {
            // Live broadcast alert event
            const newAlert: RealTimeAlert = payload.data;
            setAlerts((prev) => {
              // Deduplicate and prepend
              const filtered = prev.filter((a) => a.id !== newAlert.id);
              return [newAlert, ...filtered];
            });
            
            // Dispatch dynamic window event for global Toast notifications
            window.dispatchEvent(
              new CustomEvent('eoc-alert-toast', { detail: newAlert })
            );
          }
        } catch (err) {
          console.error('Error parsing WebSocket payload:', err);
        }
      };
    } catch (err) {
      console.error('WebSocket initialization failed:', err);
      scheduleReconnect();
    }
  };

  const scheduleReconnect = () => {
    if (reconnectTimeoutRef.current) return;
    reconnectTimeoutRef.current = window.setTimeout(() => {
      reconnectTimeoutRef.current = null;
      connect();
    }, 5000); // retry in 5s
  };

  useEffect(() => {
    connect();

    return () => {
      if (socketRef.current) {
        // Remove standard close listener to avoid loop during clean unmount
        socketRef.current.onclose = null;
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return { alerts, isConnected };
}
