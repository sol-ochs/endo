import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Account from './pages/Account';
import './App.css';

const App: React.FC = () => {
  const { loading } = useAuth();

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
    <div className="App">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/account" element={<Account />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
};

export default App;