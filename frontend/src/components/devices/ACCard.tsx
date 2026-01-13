import { DeviceCard } from './DeviceCard';
import type { ACState } from '../../hooks/useWebSocket';

interface ACCardProps {
  state: ACState;
  disabled?: boolean;
}

const modeLabels: Record<string, string> = {
  cooling: '냉방',
  heating: '난방',
  auto: '자동',
  ventilation: '송풍',
};

const fanLabels: Record<string, string> = {
  low: '약',
  medium: '중',
  high: '강',
  auto: '자동',
};

export function ACCard({ state, disabled }: ACCardProps) {
  const handlePowerToggle = async () => {
    if (disabled) return;
    const action = state.power ? 'off' : 'on';
    await fetch(`/api/device/ac/power/${action}`, { method: 'POST' });
  };

  const handleTempChange = async (delta: number) => {
    if (disabled || !state.power) return;
    const newTemp = Math.max(16, Math.min(30, state.temperature + delta));
    await fetch(`/api/device/ac/temperature/${newTemp}`, { method: 'POST' });
  };

  const handleModeChange = async (mode: string) => {
    if (disabled || !state.power) return;
    await fetch(`/api/device/ac/mode/${mode}`, { method: 'POST' });
  };

  const handleFanChange = async (speed: string) => {
    if (disabled || !state.power) return;
    await fetch(`/api/device/ac/fan/${speed}`, { method: 'POST' });
  };

  return (
    <DeviceCard
      title="에어컨"
      icon="❄️"
      isOn={state.power}
      accentColor="var(--device-ac)"
      onPowerToggle={handlePowerToggle}
    >
      <div className="device-info">
        <div className="info-row">
          <span className="info-label">온도</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button className="control-btn" onClick={() => handleTempChange(-1)}>-</button>
            <span className="info-value highlight">{state.temperature}°C</span>
            <button className="control-btn" onClick={() => handleTempChange(1)}>+</button>
          </div>
        </div>

        <div className="info-row">
          <span className="info-label">모드</span>
          <div className="button-group">
            {Object.entries(modeLabels).map(([mode, label]) => (
              <button
                key={mode}
                className={`control-btn ${state.mode === mode ? 'active' : ''}`}
                onClick={() => handleModeChange(mode)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="info-row">
          <span className="info-label">바람</span>
          <div className="button-group">
            {Object.entries(fanLabels).map(([speed, label]) => (
              <button
                key={speed}
                className={`control-btn ${state.fan_speed === speed ? 'active' : ''}`}
                onClick={() => handleFanChange(speed)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </DeviceCard>
  );
}
