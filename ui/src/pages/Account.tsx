import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { User as UserIcon, Info, LogOut, Menu, X } from 'lucide-react';
import authService from '../services/auth';
import { User, ApiError } from '../types';
import Toast from '../components/Toast';
import ProfileSection from '../components/ProfileSection';
import SecuritySettings from '../components/SecuritySettings';
import DexcomSettings from '../components/DexcomSettings';

const Account: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<Array<{id: string, message: string, type: 'success' | 'error'}>>([]);
  const [activeTab, setActiveTab] = useState('account');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const currentUser = authService.getCurrentUser();

    if (currentUser) {
      setUser(currentUser);
      setLoading(false);
    } else {
      navigate('/login');
      return;
    }
  }, [navigate]);

  const addToast = useCallback((message: string, type: 'success' | 'error') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
  }, []);

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  const handleUserUpdate = (updatedUser: User) => {
    setUser(updatedUser);
  };

  const tabs = [
    { id: 'account', label: 'Account', icon: UserIcon },
    { id: 'about', label: 'About', icon: Info },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'account':
        if (!user) return null;
        return (
          <div className="space-y-6">
            <ProfileSection
              user={user}
              onUserUpdate={handleUserUpdate}
              onToast={addToast}
            />
            <SecuritySettings onToast={addToast} />
            <DexcomSettings onToast={addToast} />
          </div>
        );
      case 'about':
        return (
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">About Endo</h2>
                <p className="card-description">
                  Learn more about the platform and get support.
                </p>
              </div>
              <div>
                <p style={{ color: 'var(--muted-foreground)', fontSize: '0.875rem' }}>
                  Coming soon.
                </p>
              </div>
            </div>
          </div>
        );
      default:
        return <div>Page not found</div>;
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-content">
          <div className="loading-spinner">⟳</div>
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Mobile menu button */}
      <button
        className="mobile-menu-btn btn btn-outline"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
      >
        {mobileMenuOpen ? <X className="icon" /> : <Menu className="icon" />}
      </button>

      {/* Navigation sidebar */}
      <div className={`dashboard-sidebar ${mobileMenuOpen ? 'open' : ''}`}>
        <div className="dashboard-sidebar-container">
          {/* Header */}
          <div className="dashboard-sidebar-header">
            <h1 className="dashboard-title">Endo</h1>
            <p className="dashboard-subtitle">Welcome, {user?.first_name}</p>
          </div>

          {/* Navigation items */}
          <nav className="dashboard-nav">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  className={`dashboard-nav-item ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setMobileMenuOpen(false);
                  }}
                >
                  <Icon className="icon" />
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="dashboard-sidebar-footer">
            <button
              className="dashboard-nav-item"
              onClick={handleLogout}
            >
              <LogOut className="icon" />
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div className="mobile-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Main content */}
      <div className="dashboard-content">
        <main className="dashboard-main">
          <div className="dashboard-main-inner">
            {renderContent()}
          </div>
        </main>
      </div>

      {/* Toast Container */}
      <div className="toast-container">
        {toasts.map(toast => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default Account;