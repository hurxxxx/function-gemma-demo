import { DeviceCard } from './DeviceCard';
import type { VacuumState } from '../../hooks/useWebSocket';

interface VacuumCardProps {
  state: VacuumState;
  disabled?: boolean;
}

const statusLabels: Record<string, string> = {
  idle: '대기 중',
  cleaning: '청소 중',
  paused: '일시정지',
  returning: '복귀 중',
};

const zoneLabels: Record<string, string> = {
  living_room: '거실',
  bedroom: '침실',
  kitchen: '주방',
  bathroom: '화장실',
};

export function VacuumCard({ state, disabled }: VacuumCardProps) {
  const handleCommand = async (command: string) => {
    if (disabled) return;
    await fetch(`/api/device/vacuum/command/${command}`, { method: 'POST' });
  };

  const handleZoneClean = async (zone: string) => {
    if (disabled) return;
    await fetch(`/api/device/vacuum/zone/${zone}`, { method: 'POST' });
  };

  const isActive = state.status === 'cleaning' || state.status === 'returning';

  return (
    <DeviceCard
      title="로봇청소기"
      icon="🤖"
      isOn={isActive}
      accentColor="var(--device-vacuum)"
    >
      <div className="device-info">
        <div className="info-row">
          <span className="info-label">상태</span>
          <span className={`status-badge ${isActive ? 'active' : 'idle'}`}>
            <span className="status-dot"></span>
            {statusLabels[state.status] || state.status}
          </span>
        </div>

        {state.current_zone && (
          <div className="info-row">
            <span className="info-label">청소 구역</span>
            <span className="info-value">{zoneLabels[state.current_zone] || state.current_zone}</span>
          </div>
        )}

        <div style={{ marginTop: '8px' }}>
          <span className="info-label" style={{ display: 'block', marginBottom: '8px' }}>컨트롤</span>
          <div className="button-group">
            <button
              className={`control-btn ${state.status === 'cleaning' ? 'active' : ''}`}
              onClick={() => handleCommand('start')}
              disabled={state.status === 'cleaning'}
            >
              시작
            </button>
            <button
              className={`control-btn ${state.status === 'paused' ? 'active' : ''}`}
              onClick={() => handleCommand('pause')}
              disabled={state.status !== 'cleaning'}
            >
              일시정지
            </button>
            <button
              className="control-btn"
              onClick={() => handleCommand('stop')}
              disabled={state.status === 'idle'}
            >
              중지
            </button>
            <button
              className={`control-btn ${state.status === 'returning' ? 'active' : ''}`}
              onClick={() => handleCommand('dock')}
            >
              충전
            </button>
          </div>
        </div>

        <div style={{ marginTop: '12px' }}>
          <span className="info-label" style={{ display: 'block', marginBottom: '8px' }}>구역 청소</span>
          <div className="button-group">
            {Object.entries(zoneLabels).map(([zone, label]) => (
              <button
                key={zone}
                className={`control-btn ${state.current_zone === zone ? 'active' : ''}`}
                onClick={() => handleZoneClean(zone)}
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
