// src/Pages/Home/Dashboard/Settings.js
import React from 'react';
import Sidebar from '../../../components/Sidebar';

function Settings() {
  return (
     <div className="dashboard-page">
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ flex: 1, padding: '30px', backgroundColor: '#f9fafb' }}>
        <h1>Settings</h1>
        <p>This is the Settings page.</p>
      </main>
    </div>
    </div>
  );
}

export default Settings;
