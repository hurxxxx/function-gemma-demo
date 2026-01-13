import type { ChangeEvent, CSSProperties } from 'react';
import { DeviceCard } from './DeviceCard';
import type { LightState } from '../../hooks/useWebSocket';

interface LightCardProps {
  state: LightState;
  disabled?: boolean;
}

export function LightCard({ state, disabled }: LightCardProps) {
  const handlePowerToggle = async () => {
    if (disabled) return;
    const action = state.power ? 'off' : 'on';
    await fetch(`/api/device/light/power/${action}`, { method: 'POST' });
  };

  const handleBrightnessChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (disabled || !state.power) return;
    const brightness = parseInt(e.target.value);
    await fetch(`/api/device/light/brightness/${brightness}`, { method: 'POST' });
  };

  const handleColorTempChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (disabled || !state.power) return;
    const temp = parseInt(e.target.value);
    await fetch(`/api/device/light/color_temp/${temp}`, { method: 'POST' });
  };

  const getColorTempLabel = (temp: number) => {
    if (temp < 3500) return '따뜻한';
    if (temp > 5500) return '시원한';
    return '자연광';
  };

  const getColorTempStyle = (temp: number) => {
    // 2700K (warm) to 6500K (cool) gradient
    const ratio = (temp - 2700) / (6500 - 2700);
    const warmColor = [255, 180, 100];
    const coolColor = [200, 220, 255];
    const r = Math.round(warmColor[0] + (coolColor[0] - warmColor[0]) * ratio);
    const g = Math.round(warmColor[1] + (coolColor[1] - warmColor[1]) * ratio);
    const b = Math.round(warmColor[2] + (coolColor[2] - warmColor[2]) * ratio);
    return `rgb(${r}, ${g}, ${b})`;
  };

  return (
    <DeviceCard
      title="거실등"
      icon="💡"
      isOn={state.power}
      accentColor="var(--device-light)"
      onPowerToggle={handlePowerToggle}
    >
      <div className="device-info">
        <div className="device-slider">
          <div className="slider-label">
            <span>밝기</span>
            <span>{state.brightness}%</span>
          </div>
          <input
            type="range"
            className="slider-input"
            min="0"
            max="100"
            value={state.brightness}
            onChange={handleBrightnessChange}
            disabled={disabled || !state.power}
            style={{ '--accent-color': 'var(--device-light)' } as CSSProperties}
          />
        </div>

        <div className="device-slider">
          <div className="slider-label">
            <span>색온도</span>
            <span style={{ color: getColorTempStyle(state.color_temp) }}>
              {state.color_temp}K ({getColorTempLabel(state.color_temp)})
            </span>
          </div>
          <input
            type="range"
            className="slider-input"
            min="2700"
            max="6500"
            step="100"
            value={state.color_temp}
            onChange={handleColorTempChange}
            disabled={disabled || !state.power}
            style={{
              '--accent-color': getColorTempStyle(state.color_temp),
              background: `linear-gradient(to right, rgb(255, 180, 100), rgb(200, 220, 255))`
            } as CSSProperties}
          />
        </div>

        <div
          className="light-preview"
          style={{
            width: '100%',
            height: '40px',
            borderRadius: 'var(--radius-sm)',
            background: state.power
              ? getColorTempStyle(state.color_temp)
              : 'var(--bg-tertiary)',
            opacity: state.power ? state.brightness / 100 : 0.3,
            transition: 'all 0.3s ease',
            marginTop: '8px'
          }}
        />
      </div>
    </DeviceCard>
  );
}
