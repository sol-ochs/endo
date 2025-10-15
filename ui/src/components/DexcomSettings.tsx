import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';
import dexcomService from '../services/dexcom';
import { ApiError } from '../types';

const DexcomSettings: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [isConnected, setIsConnected] = useState(false);
  const [lastSync, setLastSync] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const { addToast } = useToast();
  const hasHandledCallback = useRef(false);

  const checkConnectionStatus = useCallback(async () => {
    try {
      const status = await dexcomService.getConnectionStatus();
      setIsConnected(status.connected);
      setLastSync(status.lastSync);
    } catch (error) {
      const err = error as ApiError;
      // Silently handle 404 - user has no credentials yet
      if (err.status !== 404) {
        console.error('Failed to check Dexcom status:', err);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle OAuth callback - runs once on mount
  useEffect(() => {
    const dexcomParam = searchParams.get('dexcom');

    if (dexcomParam === 'connected' && !hasHandledCallback.current) {
      hasHandledCallback.current = true;

      // Clear the param from URL
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('dexcom');
      setSearchParams(newParams, { replace: true });

      // Show success toast
      addToast('Successfully connected to Dexcom!', 'success');
    }
  }, [searchParams, setSearchParams, addToast]);

  // Check connection status on mount
  useEffect(() => {
    void checkConnectionStatus();
  }, [checkConnectionStatus]);

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      const authUrl = await dexcomService.getAuthUrl();
      // Redirect to Dexcom authorization page
      window.location.href = authUrl;
    } catch (error) {
      const err = error as ApiError;
      addToast(err.message || 'Failed to connect to Dexcom', 'error');
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await dexcomService.disconnectDexcom();
      setIsConnected(false);
      setLastSync(undefined);
      addToast('Disconnected from Dexcom', 'success');
    } catch (error) {
      const err = error as ApiError;
      addToast(err.message || 'Failed to disconnect from Dexcom', 'error');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };


  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Dexcom Integration</h2>
        <p className="card-description">
          Connect your Dexcom account to receive personalized insights.
        </p>
      </div>

      <div className="field-section">
        {isLoading ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '1rem',
            backgroundColor: 'var(--muted)',
            borderRadius: '0.5rem',
            border: '1px solid var(--border)'
          }}>
            <Loader2 className="icon loading-spinner" />
            <div>
              <p style={{ margin: 0, fontWeight: 500 }}>Checking connection status...</p>
            </div>
          </div>
        ) : isConnected ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '1rem',
            backgroundColor: 'var(--success-bg)',
            borderRadius: '0.5rem',
            border: '1px solid var(--success)'
          }}>
            <CheckCircle className="icon" style={{ color: 'var(--success)' }} />
            <div>
              <p style={{ margin: 0, fontWeight: 500, color: 'var(--success)' }}>Connected</p>
              {lastSync && (
                <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--muted-foreground)' }}>
                  Last synced: {formatDate(lastSync)}
                </p>
              )}
            </div>
          </div>
        ) : (
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
                Connect your Dexcom account to receive personalized insights.
              </p>
            </div>
          </div>
        )}
      </div>

      {isConnected ? (
        <button
          className="btn btn-outline btn-single"
          onClick={handleDisconnect}
        >
          Disconnect Dexcom
        </button>
      ) : (
        <button
          className="btn btn-primary btn-single"
          onClick={handleConnect}
          disabled={isConnecting}
        >
          {isConnecting ? (
            <>
              <Loader2 className="icon loading-spinner" />
              Connecting...
            </>
          ) : (
            'Connect Dexcom'
          )}
        </button>
      )}
    </div>
  );
};

export default DexcomSettings;
