import React from 'react';

interface StatusIndicatorProps {
  label: string;
  connected: boolean;
  connectedText?: string;
  disconnectedText?: string;
  className?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  label,
  connected,
  connectedText = 'Connected',
  disconnectedText = 'Not Connected',
  className = ''
}) => {
  return (
    <div className={`field-display ${className}`}>
      <span className="field-label">{label}</span>
      <div className="status-indicator">
        <span className={`status-dot ${connected ? 'status-dot--connected' : 'status-dot--disconnected'}`} />
        <span className="field-value">
          {connected ? connectedText : disconnectedText}
        </span>
      </div>
    </div>
  );
};

export default StatusIndicator;