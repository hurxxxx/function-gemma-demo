import { DeviceCard } from './DeviceCard';
import type { VentilationState } from '../../hooks/useWebSocket';

interface VentilationCardProps {
  state: VentilationState;
  disabled?: boolean;
}

const speedLabels: Record<string, string> = {
  low: '약',
  medium: '중',
  high: '강',
  auto: '자동',
};

export function VentilationCard({ state, disabled }: VentilationCardProps) {
  const handlePowerToggle = async () => {
    if (disabled) return;
    const action = state.power ? 'off' : 'on';
    await fetch(`/api/device/ventilation/power/${action}`, { method: 'POST' });
  };

  const handleSpeedChange = async (speed: string) => {
    if (disabled || !state.power) return;
    await fetch(`/api/device/ventilation/speed/${speed}`, { method: 'POST' });
  };

  return (
    <DeviceCard
      title="환풍기"
      icon="🌀"
      isOn={state.power}
      accentColor="var(--device-ventilation)"
      onPowerToggle={handlePowerToggle}
    >
      <div className="device-info">
        <div className="info-row">
          <span className="info-label">속도</span>
          <span className="info-value">{speedLabels[state.speed] || state.speed}</span>
        </div>

        {/* 팬 애니메이션 */}
        <div
          style={{
            width: '80px',
            height: '80px',
            margin: '16px auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '48px',
            animation: state.power ? `spin ${state.speed === 'high' ? '0.5s' : state.speed === 'medium' ? '1s' : '2s'} linear infinite` : 'none',
          }}
        >
          🌀
        </div>

        <div style={{ marginTop: '8px' }}>
          <span className="info-label" style={{ display: 'block', marginBottom: '8px' }}>속도 조절</span>
          <div className="button-group" style={{ justifyContent: 'center' }}>
            {Object.entries(speedLabels).map(([speed, label]) => (
              <button
                key={speed}
                className={`control-btn ${state.speed === speed ? 'active' : ''}`}
                onClick={() => handleSpeedChange(speed)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </DeviceCard>
  );
}
