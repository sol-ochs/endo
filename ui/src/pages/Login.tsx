import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import EmailConfirmation from '../components/EmailConfirmation';
import { FormData, ApiError } from '../types';

const initialFormData: FormData = {
  email: '',
  password: '',
  first_name: '',
  last_name: ''
};

const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [pendingEmail, setPendingEmail] = useState('');
  const navigate = useNavigate();
  const { login: authLogin, register: authRegister, isAuthenticated } = useAuth();
  const { addToast } = useToast();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/account');
    }
  }, [isAuthenticated, navigate]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });

    // Clear error message when user starts typing
    if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (isLogin) {
        await authLogin(formData.email, formData.password);
        navigate('/account');
      } else {
        await authRegister(
          formData.email,
          formData.password,
          formData.first_name,
          formData.last_name
        );
        setPendingEmail(formData.email);
        setShowConfirmation(true);
        setFormData(initialFormData);
      }
    } catch (err) {
      const error = err as ApiError;
      let errorMessage = 'An error occurred';

      if (error.detail) {
        if (error.detail === 'Email already registered') {
          errorMessage = 'An account with this email already exists. Please try logging in instead.';
        } else if (error.detail === 'Incorrect email or password') {
          errorMessage = 'Invalid email or password. Please check your credentials and try again.';
        } else if (error.detail.includes('Email not confirmed')) {
          setPendingEmail(formData.email);
          setShowConfirmation(true);
          return;
        } else {
          errorMessage = error.detail;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmed = () => {
    setShowConfirmation(false);
    setPendingEmail('');
    setSuccess('Email confirmed successfully! You can now log in.');
    setIsLogin(true);
  };

  const handleBackToLogin = () => {
    setShowConfirmation(false);
    setPendingEmail('');
    setError('');
    setSuccess('');
  };

  if (showConfirmation) {
    return (
      <div className="auth-container">
        <EmailConfirmation
          email={pendingEmail}
          onConfirmed={handleConfirmed}
          onBack={handleBackToLogin}
        />
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">
          {isLogin ? 'Login to Endo' : 'Create Account'}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!isLogin && (
            <>
              <div className="form-group">
                <label className="form-label">First Name</label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  className="form-input"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Last Name</label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  className="form-input"
                  required
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="form-input"
              required
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="icon loading-spinner" />
                Loading...
              </>
            ) : (
              isLogin ? 'Login' : 'Register'
            )}
          </button>
        </form>

        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => {
            setIsLogin(!isLogin);
            setError('');
            setSuccess('');
            setFormData(initialFormData);
          }}
          style={{ marginTop: '1rem' }}
        >
          {isLogin ? 'Need an account? Register' : 'Have an account? Login'}
        </button>

        {error && <div className="status-error">{error}</div>}
        {success && <div className="status-success">{success}</div>}
      </div>
    </div>
  );
};

export default Login;