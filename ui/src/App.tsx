import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Account from './pages/Account';
import './App.css';

const App: React.FC = () => (
  <div className="App">
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/account" element={<Account />} />
      <Route path="/" element={<Navigate to="/login" replace />} />
    </Routes>
  </div>
);

export default App;