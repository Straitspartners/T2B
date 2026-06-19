import React, { useState, useEffect } from 'react';
import { Bell, User, Wifi, WifiOff, RefreshCw, Lock, Trash2, CheckCircle, XCircle, Loader } from 'lucide-react';
import Sidebar from '../../../components/Sidebar';
import { getUserName } from './useDashboard';
import './Dashboard.css';

const API = 'http://127.0.0.1:8000/api';

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${localStorage.getItem('authToken')}`,
  };
}

function StatusBadge({ status }) {
  if (status === 'connected') return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#d1fae5', color: '#065f46', padding: '4px 12px', borderRadius: 20, fontSize: 13, fontWeight: 600 }}>
      <CheckCircle size={14} /> Connected
    </span>
  );
  if (status === 'error') return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#fee2e2', color: '#991b1b', padding: '4px 12px', borderRadius: 20, fontSize: 13, fontWeight: 600 }}>
      <XCircle size={14} /> Error
    </span>
  );
  if (status === 'not_connected') return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f3f4f6', color: '#6b7280', padding: '4px 12px', borderRadius: 20, fontSize: 13, fontWeight: 600 }}>
      <WifiOff size={14} /> Not Connected
    </span>
  );
  return null;
}

function Card({ title, icon, children }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 24, marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #f3f4f6' }}>
        <span style={{ color: '#4F46E5' }}>{icon}</span>
        <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#111827' }}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

function Toast({ message, type, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);

  const colors = {
    success: { bg: '#d1fae5', color: '#065f46' },
    error: { bg: '#fee2e2', color: '#991b1b' },
    info: { bg: '#dbeafe', color: '#1e40af' },
  };
  const c = colors[type] || colors.info;

  return (
    <div style={{ position: 'fixed', top: 24, right: 24, background: c.bg, color: c.color, padding: '12px 20px', borderRadius: 10, fontWeight: 600, fontSize: 14, zIndex: 9999, boxShadow: '0 4px 12px rgba(0,0,0,0.15)', maxWidth: 360 }}>
      {message}
    </div>
  );
}

export default function Settings() {
  const [toast, setToast] = useState(null);

  // Zoho status
  const [zohoStatus, setZohoStatus] = useState(null);
  const [zohoOrgId, setZohoOrgId] = useState('');
  const [zohoLoading, setZohoLoading] = useState(true);

  // Tally test
  const [tallyHost, setTallyHost] = useState('localhost');
  const [tallyPort, setTallyPort] = useState('9000');
  const [tallyStatus, setTallyStatus] = useState(null);
  const [tallyLoading, setTallyLoading] = useState(false);

  // Password
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwLoading, setPwLoading] = useState(false);

  // Clear migration
  const [clearLoading, setClearLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const showToast = (message, type = 'success') => setToast({ message, type });

  // Load Zoho status on mount
  useEffect(() => {
    fetch(`${API}/settings/zoho-status/`, { headers: authHeaders() })
      .then(r => r.json())
      .then(data => {
        setZohoStatus(data.status);
        setZohoOrgId(data.organization_id || '');
      })
      .catch(() => setZohoStatus('error'))
      .finally(() => setZohoLoading(false));
  }, []);

  const handleTestTally = async () => {
    setTallyLoading(true);
    setTallyStatus(null);
    try {
      const r = await fetch(`${API}/settings/test-tally/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ host: tallyHost, port: parseInt(tallyPort) }),
      });
      const data = await r.json();
      setTallyStatus(data.status);
      if (data.status === 'connected') {
        showToast('Tally is reachable and responding', 'success');
      } else {
        showToast(`Tally connection failed: ${data.message}`, 'error');
      }
    } catch {
      setTallyStatus('error');
      showToast('Could not reach Tally server', 'error');
    } finally {
      setTallyLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPw || !newPw || !confirmPw) {
      showToast('All password fields are required', 'error');
      return;
    }
    if (newPw !== confirmPw) {
      showToast('New passwords do not match', 'error');
      return;
    }
    if (newPw.length < 8) {
      showToast('New password must be at least 8 characters', 'error');
      return;
    }
    setPwLoading(true);
    try {
      const r = await fetch(`${API}/settings/change-password/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
      });
      const data = await r.json();
      if (r.ok) {
        showToast('Password changed successfully', 'success');
        setCurrentPw(''); setNewPw(''); setConfirmPw('');
      } else {
        showToast(data.error || 'Failed to change password', 'error');
      }
    } catch {
      showToast('Server error. Please try again.', 'error');
    } finally {
      setPwLoading(false);
    }
  };

  const handleClearMigration = async () => {
    setClearLoading(true);
    setShowConfirm(false);
    try {
      const r = await fetch(`${API}/settings/clear-migration/`, {
        method: 'POST',
        headers: authHeaders(),
      });
      const data = await r.json();
      if (r.ok) {
        showToast(data.message, 'success');
      } else {
        showToast(data.error || 'Failed to clear data', 'error');
      }
    } catch {
      showToast('Server error. Please try again.', 'error');
    } finally {
      setClearLoading(false);
    }
  };

  const inputStyle = {
    padding: '10px 14px',
    border: '1px solid #d1d5db',
    borderRadius: 8,
    fontSize: 14,
    color: '#111827',
    background: '#fff',
    width: '100%',
    maxWidth: 400,
    outline: 'none',
  };

  const btnPrimary = {
    background: 'linear-gradient(180deg,#3a8dff 0%,#1c64f2 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    padding: '10px 24px',
    fontWeight: 600,
    fontSize: 14,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <Sidebar />
        <div className="main-content">

          {/* Header */}
          <div className="header">
            <div className="header-left">
              <h1>Settings</h1>
              <p>Manage your connections and account security</p>
            </div>
            <div className="header-right">
              <Bell className="notification-icon" />
              <div className="user-profile">
                <User className="user-icon" />
                <span>{getUserName()}</span>
              </div>
            </div>
          </div>

          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

          {/* Zoho Books Connection */}
          <Card title="Zoho Books Connection" icon={<Wifi size={20} />}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
              <span style={{ fontSize: 14, color: '#6b7280' }}>Status:</span>
              {zohoLoading ? (
                <span style={{ color: '#9ca3af', fontSize: 14 }}>Checking...</span>
              ) : (
                <StatusBadge status={zohoStatus} />
              )}
            </div>

            {zohoOrgId && (
              <div style={{ marginBottom: 16 }}>
                <span style={{ fontSize: 13, color: '#6b7280' }}>Organization ID: </span>
                <span style={{ fontSize: 13, fontWeight: 600, color: '#111827', fontFamily: 'monospace' }}>{zohoOrgId}</span>
              </div>
            )}

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button
                style={btnPrimary}
                onClick={() => window.location.href = '/setup'}
              >
                <RefreshCw size={15} />
                {zohoStatus === 'not_connected' ? 'Connect Zoho Books' : 'Reconnect'}
              </button>
              <button
                style={{ ...btnPrimary, background: '#f3f4f6', color: '#374151' }}
                onClick={() => {
                  setZohoLoading(true);
                  fetch(`${API}/settings/zoho-status/`, { headers: authHeaders() })
                    .then(r => r.json())
                    .then(data => { setZohoStatus(data.status); setZohoOrgId(data.organization_id || ''); })
                    .finally(() => setZohoLoading(false));
                }}
              >
                <RefreshCw size={15} /> Refresh Status
              </button>
            </div>

            {zohoStatus === 'not_connected' && (
              <p style={{ marginTop: 12, fontSize: 13, color: '#f59e0b', background: '#fffbeb', padding: '10px 14px', borderRadius: 8 }}>
                ⚠️ Zoho Books is not connected. Go through the setup wizard to connect.
              </p>
            )}
          </Card>

          {/* Tally Connection */}
          <Card title="Tally Connection" icon={<RefreshCw size={20} />}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 500, marginBottom: 16 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Host</label>
                <input
                  style={inputStyle}
                  value={tallyHost}
                  onChange={e => setTallyHost(e.target.value)}
                  placeholder="localhost"
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Port</label>
                <input
                  style={inputStyle}
                  value={tallyPort}
                  onChange={e => setTallyPort(e.target.value)}
                  placeholder="9000"
                  type="number"
                />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <button style={btnPrimary} onClick={handleTestTally} disabled={tallyLoading}>
                {tallyLoading ? <Loader size={15} className="spin" /> : <Wifi size={15} />}
                {tallyLoading ? 'Testing...' : 'Test Connection'}
              </button>
              {tallyStatus && <StatusBadge status={tallyStatus} />}
            </div>

            <p style={{ marginTop: 12, fontSize: 12, color: '#9ca3af' }}>
              Make sure TallyPrime is open and the company is loaded before testing.
            </p>
          </Card>

          {/* Change Password */}
          <Card title="Change Password" icon={<Lock size={20} />}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 400 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Current Password</label>
                <input style={inputStyle} type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} placeholder="Enter current password" />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>New Password</label>
                <input style={inputStyle} type="password" value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="At least 8 characters" />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Confirm New Password</label>
                <input style={inputStyle} type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} placeholder="Repeat new password" />
              </div>
              <button style={{ ...btnPrimary, alignSelf: 'flex-start' }} onClick={handleChangePassword} disabled={pwLoading}>
                {pwLoading ? <Loader size={15} /> : <Lock size={15} />}
                {pwLoading ? 'Saving...' : 'Update Password'}
              </button>
            </div>
          </Card>

          {/* Danger Zone */}
          <Card title="Danger Zone" icon={<Trash2 size={20} />}>
            <p style={{ fontSize: 14, color: '#6b7280', marginBottom: 20 }}>
              Reset all Zoho migration IDs so every record gets re-pushed on the next sync. Use this if you deleted data in Zoho and want to start fresh. <strong>This does not delete your Tally data.</strong>
            </p>

            {!showConfirm ? (
              <button
                style={{ background: '#fee2e2', color: '#dc2626', border: '1px solid #fca5a5', borderRadius: 8, padding: '10px 24px', fontWeight: 600, fontSize: 14, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8 }}
                onClick={() => setShowConfirm(true)}
              >
                <Trash2 size={15} /> Clear Migration Data
              </button>
            ) : (
              <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 10, padding: 16, maxWidth: 440 }}>
                <p style={{ margin: '0 0 14px', fontSize: 14, fontWeight: 600, color: '#92400e' }}>
                  Are you sure? This will reset all Zoho IDs and the next sync will re-create everything in Zoho Books.
                </p>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    style={{ background: '#dc2626', color: '#fff', border: 'none', borderRadius: 8, padding: '9px 20px', fontWeight: 600, fontSize: 14, cursor: 'pointer' }}
                    onClick={handleClearMigration}
                    disabled={clearLoading}
                  >
                    {clearLoading ? 'Clearing...' : 'Yes, clear it'}
                  </button>
                  <button
                    style={{ background: '#f3f4f6', color: '#374151', border: 'none', borderRadius: 8, padding: '9px 20px', fontWeight: 600, fontSize: 14, cursor: 'pointer' }}
                    onClick={() => setShowConfirm(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </Card>

        </div>
      </div>
    </div>
  );
}