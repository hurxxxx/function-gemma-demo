import type { CSSProperties, ReactNode } from 'react';
import './DeviceCard.css';

interface DeviceCardProps {
  title: string;
  icon: string;
  isOn: boolean;
  accentColor: string;
  children: ReactNode;
  onPowerToggle?: () => void;
}

export function DeviceCard({
  title,
  icon,
  isOn,
  accentColor,
  children,
  onPowerToggle
}: DeviceCardProps) {
  return (
    <div
      className={`device-card ${isOn ? 'on' : 'off'}`}
      style={{ '--accent-color': accentColor } as CSSProperties}
    >
      <div className="device-header">
        <div className="device-icon">{icon}</div>
        <h3 className="device-title">{title}</h3>
        {onPowerToggle && (
          <button
            className={`power-toggle ${isOn ? 'on' : 'off'}`}
            onClick={onPowerToggle}
          >
            {isOn ? 'ON' : 'OFF'}
          </button>
        )}
      </div>
      <div className="device-content">
        {children}
      </div>
    </div>
  );
}
