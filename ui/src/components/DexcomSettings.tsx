import React from 'react';
import { AlertCircle } from 'lucide-react';

interface DexcomSettingsProps {
  onToast?: (message: string, type: 'success' | 'error') => void;
}

const DexcomSettings: React.FC<DexcomSettingsProps> = () => {
  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Dexcom Integration</h2>
        <p className="card-description">
          Connect your Dexcom CGM to track glucose levels.
        </p>
      </div>

      <div className="field-section">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '1rem',
          backgroundColor: 'var(--muted)',
          borderRadius: '0.5rem',
          border: '1px solid var(--border)'
        }}>
          <AlertCircle className="icon" style={{ color: 'var(--muted-foreground)' }} />
          <div>
            <p style={{ margin: 0, fontWeight: 500 }}>Not Connected</p>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--muted-foreground)' }}>
              Integration under development
            </p>
          </div>
        </div>
      </div>

      <button
        className="btn btn-outline btn-single"
        disabled
        style={{ opacity: 0.6, cursor: 'not-allowed' }}
      >
        Connect Dexcom (Coming Soon)
      </button>
    </div>
  );
};

export default DexcomSettings;