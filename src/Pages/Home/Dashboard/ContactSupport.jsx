import React from 'react';
import Sidebar from '../../../components/Sidebar';

function Contact() {
  return (
     <div className="dashboard-page">
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ flex: 1, padding: '30px', backgroundColor: '#f9fafb' }}>
        <h1>Contact Support</h1>
        <p>You can reach our support team here.</p>
      </main>
    </div>
    </div>
  );
}

export default Contact;
