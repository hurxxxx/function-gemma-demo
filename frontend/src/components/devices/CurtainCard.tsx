import type { ChangeEvent, CSSProperties } from 'react';
import { DeviceCard } from './DeviceCard';
import type { CurtainState } from '../../hooks/useWebSocket';

interface CurtainCardProps {
  state: CurtainState;
  disabled?: boolean;
}

export function CurtainCard({ state, disabled }: CurtainCardProps) {
  const handleCommand = async (command: string) => {
    if (disabled) return;
    await fetch(`/api/device/curtain/command/${command}`, { method: 'POST' });
  };

  const handlePositionChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    const position = parseInt(e.target.value);
    await fetch(`/api/device/curtain/position/${position}`, { method: 'POST' });
  };

  const isOpen = state.position > 50;
  const positionLabel = state.position === 0 ? '닫힘' : state.position === 100 ? '열림' : `${state.position}%`;

  return (
    <DeviceCard
      title="전동커튼"
      icon="🪟"
      isOn={isOpen}
      accentColor="var(--device-curtain)"
    >
      <div className="device-info">
        <div className="info-row">
          <span className="info-label">상태</span>
          <span className="info-value highlight">{positionLabel}</span>
        </div>

        <div className="device-slider">
          <div className="slider-label">
            <span>위치</span>
            <span>{state.position}%</span>
          </div>
          <input
            type="range"
            className="slider-input"
            min="0"
            max="100"
            value={state.position}
            onChange={handlePositionChange}
            disabled={disabled}
            style={{ '--accent-color': 'var(--device-curtain)' } as CSSProperties}
          />
          <div className="slider-label" style={{ marginTop: '4px' }}>
            <span style={{ fontSize: '0.7rem' }}>닫힘</span>
            <span style={{ fontSize: '0.7rem' }}>열림</span>
          </div>
        </div>

        {/* 커튼 시각화 */}
        <div
          style={{
            width: '100%',
            height: '60px',
            position: 'relative',
            background: 'linear-gradient(to bottom, #87CEEB, #E0F4FF)',
            borderRadius: 'var(--radius-sm)',
            overflow: 'hidden',
            marginTop: '8px'
          }}
        >
          {/* 왼쪽 커튼 */}
          <div
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: `${(100 - state.position) / 2}%`,
              height: '100%',
              background: 'var(--device-curtain)',
              transition: 'width 0.5s ease',
              boxShadow: '2px 0 8px rgba(0,0,0,0.1)'
            }}
          />
          {/* 오른쪽 커튼 */}
          <div
            style={{
              position: 'absolute',
              right: 0,
              top: 0,
              width: `${(100 - state.position) / 2}%`,
              height: '100%',
              background: 'var(--device-curtain)',
              transition: 'width 0.5s ease',
              boxShadow: '-2px 0 8px rgba(0,0,0,0.1)'
            }}
          />
        </div>

        <div style={{ marginTop: '12px' }}>
          <div className="button-group">
            <button
              className={`control-btn ${state.position === 100 ? 'active' : ''}`}
              onClick={() => handleCommand('open')}
            >
              열기
            </button>
            <button
              className="control-btn"
              onClick={() => handleCommand('stop')}
            >
              멈춤
            </button>
            <button
              className={`control-btn ${state.position === 0 ? 'active' : ''}`}
              onClick={() => handleCommand('close')}
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </DeviceCard>
  );
}
