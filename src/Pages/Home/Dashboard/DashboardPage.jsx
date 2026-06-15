import React from 'react';
import { Bell, User, Database, BarChart3, CreditCard } from 'lucide-react';
import Sidebar from '../../../components/Sidebar';
import './Dashboard.css';
import { getUserName } from './useDashboard';

// ---- Snackbar ----
export function SnackbarAlert({ alert, onClose }) {
  if (!alert.show) return null;
  const icons = { error: '❌', success: '✅', warning: '⚠️', info: 'ℹ️' };
  return (
    <div className={`snackbar-alert ${alert.type}`}>
      <div className="snackbar-content">
        <div className="snackbar-icon">{icons[alert.type] || 'ℹ️'}</div>
        <div className="snackbar-message">
          {alert.message.split('\n').map((line, i) => (
            <div key={i} className="snackbar-line">{line}</div>
          ))}
        </div>
        <button className="snackbar-close" onClick={onClose}>×</button>
      </div>
    </div>
  );
}

// ---- Stat Cards row ----
export function StatsRow({ stats, cardConfig }) {
  const defaults = [
    { key: 'dataFetchedFromTally',  label: 'Data Fetched from Tally',        icon: <Database size={24} />, color: 'blue',   change: '↗ Live Data' },
    { key: 'dataMigratedToZoho',    label: 'Data Migrated to Zoho Books',     icon: <BarChart3 size={24} />, color: 'orange', change: '↗ Live Data' },
    { key: 'pendingMigration',      label: 'Pending Migration',               icon: <CreditCard size={24} />, color: 'yellow', change: 'Live Data' },
  ];
  const cards = cardConfig || defaults;

  return (
    <div className="stats-grid">
      {cards.map((card) => (
        <div className={`stat-card ${card.color}`} key={card.key}>
          <div className="stat-icon">{card.icon}</div>
          <div className="stat-content">
            <h3>{card.label}</h3>
            <div className="stat-number">
              {stats.loading ? 'Loading…' : (stats[card.key] ?? 0).toLocaleString()}
            </div>
            <div className="stat-change positive">{card.change}</div>
          </div>
          <div className="stat-chart">
            <svg width="100" height="40" viewBox="0 0 100 40">
              <path d="M5,35 Q25,20 45,25 T85,15" stroke={card.stroke || '#4F46E5'} strokeWidth="2" fill="none" />
            </svg>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---- Full page shell ----
export default function DashboardPage({ title, subtitle, stats, alert, onHideAlert, onRefresh, children, cardConfig }) {
  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <Sidebar />
        <div className="main-content">
          {/* Header */}
          <div className="header">
            <div className="header-left">
              <h1>{title}</h1>
              <p>{subtitle || 'Monitor and manage your entire data migration process from a single dashboard'}</p>
            </div>
            <div className="header-right">
              {onRefresh && (
                <button onClick={onRefresh} className="refresh-btn" title="Refresh Data">🔄</button>
              )}
              <Bell className="notification-icon" />
              <div className="user-profile">
                <User className="user-icon" />
                <span>{getUserName()}</span>
              </div>
            </div>
          </div>

          {/* Alert */}
          <SnackbarAlert alert={alert} onClose={onHideAlert} />

          {/* Stats */}
          <StatsRow stats={stats} cardConfig={cardConfig} />

          {/* Page body */}
          {children}
        </div>
      </div>
    </div>
  );
}