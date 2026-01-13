import { DeviceCard } from './DeviceCard';
import type { TVState } from '../../hooks/useWebSocket';

interface TVCardProps {
  state: TVState;
  disabled?: boolean;
}

const apps = ['Netflix', 'YouTube', 'Disney+', 'Wavve'];

export function TVCard({ state, disabled }: TVCardProps) {
  const handlePowerToggle = async () => {
    if (disabled) return;
    const action = state.power ? 'off' : 'on';
    await fetch(`/api/device/tv/power/${action}`, { method: 'POST' });
  };

  const handleChannelChange = async (delta: number) => {
    if (disabled || !state.power) return;
    const newChannel = Math.max(1, Math.min(100, state.channel + delta));
    await fetch(`/api/device/tv/channel/${newChannel}`, { method: 'POST' });
  };

  const handleVolumeChange = async (delta: number) => {
    if (disabled || !state.power) return;
    const newVolume = Math.max(0, Math.min(100, state.volume + delta));
    await fetch(`/api/device/tv/volume/${newVolume}`, { method: 'POST' });
  };

  const handleAppLaunch = async (app: string) => {
    if (disabled || !state.power) return;
    await fetch(`/api/device/tv/app/${encodeURIComponent(app)}`, { method: 'POST' });
  };

  return (
    <DeviceCard
      title="TV"
      icon="📺"
      isOn={state.power}
      accentColor="var(--device-tv)"
      onPowerToggle={handlePowerToggle}
    >
      <div className="device-info">
        <div className="info-row">
          <span className="info-label">채널</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button className="control-btn" onClick={() => handleChannelChange(-1)}>-</button>
            <span className="info-value highlight">{state.channel}</span>
            <button className="control-btn" onClick={() => handleChannelChange(1)}>+</button>
          </div>
        </div>

        <div className="info-row">
          <span className="info-label">볼륨</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button className="control-btn" onClick={() => handleVolumeChange(-5)}>-</button>
            <span className="info-value">{state.volume}</span>
            <button className="control-btn" onClick={() => handleVolumeChange(5)}>+</button>
          </div>
        </div>

        {state.current_app && (
          <div className="info-row">
            <span className="info-label">현재 앱</span>
            <span className="status-badge active">
              <span className="status-dot"></span>
              {state.current_app}
            </span>
          </div>
        )}

        <div style={{ marginTop: '8px' }}>
          <span className="info-label" style={{ display: 'block', marginBottom: '8px' }}>앱</span>
          <div className="button-group">
            {apps.map((app) => (
              <button
                key={app}
                className={`control-btn ${state.current_app === app ? 'active' : ''}`}
                onClick={() => handleAppLaunch(app)}
              >
                {app}
              </button>
            ))}
          </div>
        </div>
      </div>
    </DeviceCard>
  );
}
