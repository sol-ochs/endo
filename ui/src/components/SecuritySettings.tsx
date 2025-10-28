import React from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/auth';
import { useToast } from '../contexts/ToastContext';
import { ApiError } from '../types';
import DisplayField from './DisplayField';

const SecuritySettings: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const handleDeactivateAccount = async () => {
    try {
      await authService.deactivateAccount();
      addToast('Account deactivated successfully.', 'success');
      navigate('/login');
    } catch (err) {
      const error = err as ApiError;
      addToast(error.message || 'Failed to deactivate account. Please try again.', 'error');
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Account Security</h2>
        <p className="card-description">
          Manage your account security and data.
        </p>
      </div>

      <div className="field-section">
        <DisplayField label="Password" value="••••••••••••" />
        <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: 'var(--muted)', borderRadius: 'var(--radius)' }}>
          <p className="text-sm text-muted" style={{ margin: 0 }}>
            To change your password, please use the "Forgot Password" option on the login page.
          </p>
        </div>
      </div>

      <div className="mb-6" style={{ paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
        <div className="mb-4">
          <h4 style={{ fontSize: '0.9rem', fontWeight: 500, marginBottom: '0.25rem' }}>Account Deactivation</h4>
          <p className="text-sm text-muted" style={{ margin: 0 }}>
            Temporarily disable your account. You can reactivate by logging in again.
          </p>
        </div>
        <button onClick={handleDeactivateAccount} className="btn btn-secondary btn-single">
          Deactivate Account
        </button>
      </div>
    </div>
  );
};

export default SecuritySettings;