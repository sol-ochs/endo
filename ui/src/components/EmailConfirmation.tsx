import React, { useState } from 'react';
import { Loader2, Mail, RotateCcw } from 'lucide-react';
import authService from '../services/auth';
import { ApiError } from '../types';

interface EmailConfirmationProps {
  email: string;
  onConfirmed: () => void;
  onBack: () => void;
}

const EmailConfirmation: React.FC<EmailConfirmationProps> = ({ email, onConfirmed, onBack }) => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await authService.confirmEmail(email, code);
      setSuccess('Email confirmed successfully!');
      setTimeout(() => onConfirmed(), 1500);
    } catch (err) {
      const error = err as ApiError;
      let errorMessage = 'Confirmation failed';

      if (error.detail) {
        if (error.detail.includes('Invalid verification code')) {
          errorMessage = 'Invalid verification code. Please check and try again.';
        } else if (error.detail.includes('expired')) {
          errorMessage = 'Verification code has expired. Please request a new one.';
        } else {
          errorMessage = error.detail;
        }
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError('');
    setSuccess('');

    try {
      await authService.resendConfirmation(email);
      setSuccess('New verification code sent to your email.');
      setCode('');
    } catch (err) {
      const error = err as ApiError;
      setError(error.detail || 'Failed to resend code');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="auth-card">
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <Mail size={48} style={{ color: '#6b7280', marginBottom: '1rem' }} />
        <h1 className="auth-title">Confirm Your Email</h1>
        <p style={{ color: '#6b7280', fontSize: '0.9rem', lineHeight: '1.4' }}>
          We've sent a verification code to<br />
          <strong>{email}</strong>
        </p>
      </div>

      <form onSubmit={handleConfirm} className="space-y-6">
        <div className="form-group">
          <label className="form-label">Verification Code</label>
          <input
            type="text"
            value={code}
            onChange={(e) => {
              setCode(e.target.value.replace(/[^0-9]/g, '').slice(0, 6));
              if (error) setError('');
            }}
            className="form-input"
            placeholder="Enter 6-digit code"
            maxLength={6}
            required
            style={{
              textAlign: 'center',
              fontSize: '1.25rem',
              letterSpacing: '0.25rem',
              fontFamily: 'monospace'
            }}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading || code.length !== 6}>
          {loading ? (
            <>
              <Loader2 className="icon loading-spinner" />
              Confirming...
            </>
          ) : (
            'Confirm Email'
          )}
        </button>
      </form>

      <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={handleResend}
          disabled={resending}
          style={{ marginRight: '0.75rem' }}
        >
          {resending ? (
            <>
              <Loader2 className="icon loading-spinner" />
              Sending...
            </>
          ) : (
            <>
              <RotateCcw className="icon" />
              Resend Code
            </>
          )}
        </button>

        <button
          type="button"
          className="btn btn-ghost"
          onClick={onBack}
        >
          Back to Login
        </button>
      </div>

      {error && <div className="status-error">{error}</div>}
      {success && <div className="status-success">{success}</div>}
    </div>
  );
};

export default EmailConfirmation;