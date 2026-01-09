import { useState } from 'react';
import type { ACState } from '../hooks/useWebSocket';
import './ManualControls.css';

interface ManualControlsProps {
  state: ACState;
  disabled?: boolean;
}

export function ManualControls({ state, disabled }: ManualControlsProps) {
  const [error, setError] = useState<string | null>(null);

  const post = async (path: string, body?: Record<string, unknown>) => {
    try {
      const options: RequestInit = { method: 'POST' };
      if (body) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(body);
      }

      const response = await fetch(`/api${path}`, options);
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || '요청 실패');
      }
      setError(null);
    } catch (err) {
      console.error('Manual control request failed:', err);
      setError('서버 연결 실패');
    }
  };

  const clampTemp = (value: number, min: number, max: number) =>
    Math.min(max, Math.max(min, value));

  const handlePowerToggle = () => {
    if (disabled) return;
    post(`/ac/power/${state.power ? 'off' : 'on'}`);
  };

  const handleTemperatureStep = (delta: number) => {
    if (disabled) return;
    const nextTemp = clampTemp(state.temperature + delta, 16, 30);
    post(`/ac/temperature/${nextTemp}`);
  };

  const handleMode = (mode: string) => {
    if (disabled) return;
    post(`/ac/mode/${mode}`);
  };

  const handleFanSpeed = (speed: string) => {
    if (disabled) return;
    post(`/ac/fan/${speed}`);
  };

  const handleIndoorTemp = (delta: number) => {
    if (disabled) return;
    const nextTemp = clampTemp(state.indoor_temperature + delta, -20, 50);
    post('/environment', { indoor_temperature: nextTemp });
  };

  const handleOutdoorTemp = (delta: number) => {
    if (disabled) return;
    const nextTemp = clampTemp(state.outdoor_temperature + delta, -20, 50);
    post('/environment', { outdoor_temperature: nextTemp });
  };

  return (
    <div className="manual-controls">
      <div className="manual-header">직접 컨트롤</div>

      <div className="manual-row">
        <span className="manual-label">전원</span>
        <button
          type="button"
          className={`toggle-button ${state.power ? 'on' : 'off'}`}
          onClick={handlePowerToggle}
          disabled={disabled}
        >
          {state.power ? '켜짐' : '꺼짐'}
        </button>
      </div>

      <div className="manual-row">
        <span className="manual-label">목표 온도</span>
        <div className="stepper">
          <button
            type="button"
            onClick={() => handleTemperatureStep(-1)}
            disabled={disabled}
          >
            -
          </button>
          <span className="stepper-value">{state.temperature}°C</span>
          <button
            type="button"
            onClick={() => handleTemperatureStep(1)}
            disabled={disabled}
          >
            +
          </button>
        </div>
      </div>

      <div className="manual-row">
        <span className="manual-label">모드</span>
        <div className="button-group">
          {[
            { value: 'cooling', label: '냉방' },
            { value: 'heating', label: '난방' },
            { value: 'auto', label: '자동' },
            { value: 'ventilation', label: '송풍' },
          ].map((mode) => (
            <button
              key={mode.value}
              type="button"
              className={state.mode === mode.value ? 'active' : ''}
              onClick={() => handleMode(mode.value)}
              disabled={disabled}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      <div className="manual-row">
        <span className="manual-label">팬 속도</span>
        <div className="button-group">
          {[
            { value: 'low', label: '약' },
            { value: 'medium', label: '중' },
            { value: 'high', label: '강' },
            { value: 'auto', label: '자동' },
          ].map((speed) => (
            <button
              key={speed.value}
              type="button"
              className={state.fan_speed === speed.value ? 'active' : ''}
              onClick={() => handleFanSpeed(speed.value)}
              disabled={disabled}
            >
              {speed.label}
            </button>
          ))}
        </div>
      </div>

      <div className="manual-divider" />

      <div className="manual-row">
        <span className="manual-label">실내 온도</span>
        <div className="stepper">
          <button
            type="button"
            onClick={() => handleIndoorTemp(-1)}
            disabled={disabled}
          >
            -
          </button>
          <span className="stepper-value">{state.indoor_temperature}°C</span>
          <button
            type="button"
            onClick={() => handleIndoorTemp(1)}
            disabled={disabled}
          >
            +
          </button>
        </div>
      </div>

      <div className="manual-row">
        <span className="manual-label">외기 온도</span>
        <div className="stepper">
          <button
            type="button"
            onClick={() => handleOutdoorTemp(-1)}
            disabled={disabled}
          >
            -
          </button>
          <span className="stepper-value">{state.outdoor_temperature}°C</span>
          <button
            type="button"
            onClick={() => handleOutdoorTemp(1)}
            disabled={disabled}
          >
            +
          </button>
        </div>
      </div>

      {error && <div className="manual-error">{error}</div>}
    </div>
  );
}
