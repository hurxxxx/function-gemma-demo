import { useState, useEffect, useCallback, useRef } from 'react';

// 개별 기기 상태 인터페이스
export interface ACState {
  power: boolean;
  temperature: number;
  mode: string;
  fan_speed: string;
}

export interface TVState {
  power: boolean;
  channel: number;
  volume: number;
  current_app: string | null;
}

export interface LightState {
  power: boolean;
  brightness: number;
  color_temp: number;
}

export interface VacuumState {
  power: boolean;
  status: string;
  current_zone: string | null;
}

export interface AudioState {
  power: boolean;
  volume: number;
  playback: string;
  current_playlist: string | null;
}

export interface CurtainState {
  position: number;
  status: string;
}

export interface VentilationState {
  power: boolean;
  speed: string;
}

// 전체 홈 상태 인터페이스
export interface HomeState {
  ac: ACState;
  tv: TVState;
  light: LightState;
  vacuum: VacuumState;
  audio: AudioState;
  curtain: CurtainState;
  ventilation: VentilationState;
}

interface WebSocketMessage {
  type: string;
  state?: HomeState;
}

// 초기 홈 상태
const initialHomeState: HomeState = {
  ac: {
    power: false,
    temperature: 24,
    mode: 'cooling',
    fan_speed: 'auto',
  },
  tv: {
    power: false,
    channel: 1,
    volume: 30,
    current_app: null,
  },
  light: {
    power: false,
    brightness: 100,
    color_temp: 4000,
  },
  vacuum: {
    power: false,
    status: 'idle',
    current_zone: null,
  },
  audio: {
    power: false,
    volume: 30,
    playback: 'stopped',
    current_playlist: null,
  },
  curtain: {
    position: 100,
    status: 'stopped',
  },
  ventilation: {
    power: false,
    speed: 'auto',
  },
};

export function useWebSocket(url: string) {
  const [state, setState] = useState<HomeState>(initialHomeState);
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
