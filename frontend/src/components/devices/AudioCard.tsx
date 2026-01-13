import type { ChangeEvent, CSSProperties } from 'react';
import { DeviceCard } from './DeviceCard';
import type { AudioState } from '../../hooks/useWebSocket';

interface AudioCardProps {
  state: AudioState;
  disabled?: boolean;
}

const playlists = ['Jazz', 'Classical', 'Pop', 'Chill'];

const playbackIcons: Record<string, string> = {
  playing: '▶',
  paused: '⏸',
  stopped: '⏹',
};

export function AudioCard({ state, disabled }: AudioCardProps) {
  const handlePowerToggle = async () => {
    if (disabled) return;
    const action = state.power ? 'off' : 'on';
    await fetch(`/api/device/audio/power/${action}`, { method: 'POST' });
  };

  const handleVolumeChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (disabled || !state.power) return;
    const volume = parseInt(e.target.value);
    await fetch(`/api/device/audio/volume/${volume}`, { method: 'POST' });
  };

  const handlePlayback = async (command: string) => {
    if (disabled || !state.power) return;
    await fetch(`/api/device/audio/playback/${command}`, { method: 'POST' });
  };

  const handlePlaylist = async (playlist: string) => {
    if (disabled || !state.power) return;
    await fetch(`/api/device/audio/playlist/${encodeURIComponent(playlist.toLowerCase())}`, { method: 'POST' });
  };

  const isPlaying = state.playback === 'playing';

  return (
    <DeviceCard
      title="오디오"
      icon="🎵"
      isOn={state.power}
      accentColor="var(--device-audio)"
      onPowerToggle={handlePowerToggle}
    >
      <div className="device-info">
        <div className="info-row">
          <span className="info-label">상태</span>
          <span className={`status-badge ${isPlaying ? 'active' : 'idle'}`}>
            <span>{playbackIcons[state.playback]}</span>
            {state.playback === 'playing' ? '재생 중' : state.playback === 'paused' ? '일시정지' : '정지'}
          </span>
        </div>

        {state.current_playlist && (
          <div className="info-row">
            <span className="info-label">플레이리스트</span>
            <span className="info-value">{state.current_playlist}</span>
          </div>
        )}

        <div className="device-slider">
          <div className="slider-label">
            <span>볼륨</span>
            <span>{state.volume}%</span>
          </div>
          <input
            type="range"
            className="slider-input"
            min="0"
            max="100"
            value={state.volume}
            onChange={handleVolumeChange}
            disabled={disabled || !state.power}
            style={{ '--accent-color': 'var(--device-audio)' } as CSSProperties}
          />
        </div>

        <div style={{ marginTop: '8px' }}>
          <span className="info-label" style={{ display: 'block', marginBottom: '8px' }}>재생</span>
          <div className="button-group">
            <button
              className={`control-btn ${state.playback === 'playing' ? 'active' : ''}`}
              onClick={() => handlePlayback('play')}
            >
              ▶ 재생
            </button>
            <button
              className={`control-btn ${state.playback === 'paused' ? 'active' : ''}`}
              onClick={() => handlePlayback('pause')}
            >
              ⏸ 일시정지
            </button>
            <button
              className="control-btn"
              onClick={() => handlePlayback('stop')}
            >
              ⏹ 정지
            </button>
          </div>
        </div>

        <div style={{ marginTop: '12px' }}>
          <span className="info-label" style={{ display: 'block', marginBottom: '8px' }}>플레이리스트</span>
          <div className="button-group">
            {playlists.map((playlist) => (
              <button
                key={playlist}
                className={`control-btn ${state.current_playlist?.toLowerCase() === playlist.toLowerCase() ? 'active' : ''}`}
                onClick={() => handlePlaylist(playlist)}
              >
                {playlist}
              </button>
            ))}
          </div>
        </div>
      </div>
    </DeviceCard>
  );
}
