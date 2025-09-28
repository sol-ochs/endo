import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import dexcomService from '../services/dexcom';
import { CallbackStatus, ApiError } from '../types';

const DexcomCallback: React.FC = () => {
  const [status, setStatus] = useState<CallbackStatus>('processing');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const error = searchParams.get('error');

      if (error) {
        setStatus('error');
        setError('Dexcom authorization was denied or failed');
        return;
      }

      if (!code) {
        setStatus('error');
        setError('No authorization code received from Dexcom');
        return;
      }

      try {
        await dexcomService.handleCallback(code);
        setStatus('success');
        setTimeout(() => {
          navigate('/account');
        }, 2000);
      } catch (err) {
        const error = err as ApiError;
        setStatus('error');
        setError(error.message || 'Failed to complete Dexcom connection');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">Connecting to Dexcom</h1>

        {status === 'processing' && (
          <div className="text-center">
            <div className="loading-content" style={{ justifyContent: 'center', marginBottom: '1rem' }}>
              <Loader2 className="icon-lg loading-spinner" />
            </div>
            <p>Processing your Dexcom authorization...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="status-success" style={{ justifyContent: 'center', marginBottom: '1rem' }}>
              <CheckCircle className="icon-lg" />
              Successfully connected to Dexcom!
            </div>
            <p>Redirecting to dashboard...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--destructive)', marginBottom: '1rem' }}>
              <XCircle className="icon-lg" />
              <span>Connection failed</span>
            </div>
            <p className="status-error">{error}</p>
            <button
              onClick={() => navigate('/account')}
              className="btn btn-primary"
              style={{ marginTop: '1.5rem' }}
            >
              Return to Account
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DexcomCallback;