import type { ACState } from '../hooks/useWebSocket';
import './ACDisplay.css';

interface ACDisplayProps {
  state: ACState;
}

const modeIcons: Record<string, string> = {
  cooling: '❄️',
  heating: '🔥',
  auto: '🔄',
  ventilation: '💨',
};

const modeLabels: Record<string, string> = {
  cooling: '냉방',
  heating: '난방',
  auto: '자동',
  ventilation: '송풍',
};

const fanSpeedLabels: Record<string, string> = {
  low: '약',
  medium: '중',
  high: '강',
  auto: '자동',
};

export function ACDisplay({ state }: ACDisplayProps) {
  return (
    <div className={`ac-display ${state.power ? 'power-on' : 'power-off'}`}>
      <div className="ac-header">
        <div className={`power-indicator ${state.power ? 'on' : 'off'}`}>
          {state.power ? 'ON' : 'OFF'}
        </div>
        <div className="ac-title">CAR A/C</div>
      </div>

      <div className="temperature-display">
        <span className="temp-value">{state.temperature}</span>
        <span className="temp-unit">°C</span>
      </div>

      <div className="environment-display">
        <div className="environment-item">
          <div className="environment-label">실내</div>
          <div className="environment-value">
            {state.indoor_temperature}°C
          </div>
        </div>
        <div className="environment-item">
          <div className="environment-label">외기</div>
          <div className="environment-value">
            {state.outdoor_temperature}°C
          </div>
        </div>
      </div>

      <div className="ac-controls">
        <div className="control-item">
          <div className="control-icon">{modeIcons[state.mode] || '❄️'}</div>
          <div className="control-label">모드</div>
          <div className="control-value">{modeLabels[state.mode] || state.mode}</div>
        </div>

        <div className="control-item">
          <div className="control-icon">🌀</div>
          <div className="control-label">팬 속도</div>
          <div className="control-value">{fanSpeedLabels[state.fan_speed] || state.fan_speed}</div>
        </div>
      </div>

      <div className="temp-range">
        <div className="temp-bar">
          <div
            className="temp-fill"
            style={{
              width: `${((state.temperature - 16) / 14) * 100}%`
            }}
          />
          <div
            className="temp-marker"
            style={{
              left: `${((state.temperature - 16) / 14) * 100}%`
            }}
          />
        </div>
        <div className="temp-labels">
          <span>16°C</span>
          <span>30°C</span>
        </div>
      </div>
    </div>
  );
}
