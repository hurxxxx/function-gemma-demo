import { useState, useEffect, useCallback, useRef } from 'react';

export interface ACState {
  power: boolean;
  temperature: number;
  indoor_temperature: number;
  outdoor_temperature: number;
  fan_speed: string;
  mode: string;
}

interface WebSocketMessage {
  type: string;
  state?: ACState;
}

export function useWebSocket(url: string) {
  const [state, setState] = useState<ACState>({
    power: false,
    temperature: 24,
    indoor_temperature: 26,
    outdoor_temperature: 32,
    fan_speed: 'auto',
    mode: 'cooling',
  });
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string' && event.data.trim() === 'pong') {
        return;
      }

      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        if (data.type === 'state_update' && data.state) {
          setState(data.state);
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      // 재연결 시도
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [url]);

  useEffect(() => {
    connect();

    // Ping 주기적으로 전송 (연결 유지)
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return { state, connected };
}
