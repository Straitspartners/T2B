import React, { useState, useEffect } from 'react';
import { Bell, User, BarChart3, Database } from 'lucide-react';
import './Dashboard.css';
import Sidebar from '../../../components/Sidebar';

function Transactions() {
  const userName =
    JSON.parse(localStorage.getItem("userData") || '{}')?.name ||
    localStorage.getItem("userName") ||
    "User";

  const [activities, setActivities] = useState([]);
  const [counts, setCounts] = useState({ invoices: 0, receipts: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchTransactions = async () => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) throw new Error('Authentication token not found. Please login again.');

      const response = await fetch('http://127.0.0.1:8000/api/get-transactions/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (!response.ok) {
        const err = await response.text();
        throw new Error(`Failed to fetch transactions: ${response.status} - ${err}`);
      }

      const data = await response.json();
      setActivities(data.activities || []);
      setCounts(data.counts || {});
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const totalFetched = counts.invoices + counts.receipts;

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <Sidebar />
        <div className="main-content">
          {/* Header */}
          <div className="header">
            <div className="header-left">
              <h1>Transactions</h1>
              <p>Monitor and manage your entire data migration process from a single dashboard</p>
            </div>
            <div className="header-right">
              <Bell className="notification-icon" />
              <div className="user-profile">
                <User className="user-icon" />
                <span>{userName}</span>
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div style={{ background: '#fee2e2', color: '#dc2626', padding: '12px', borderRadius: '8px', margin: '10px 0' }}>
              ❌ {error}
            </div>
          )}

          {/* Stats Cards */}
          <div className="stats-grid">
            <div className="stat-card blue">
              <div className="stat-icon"><Database size={24} /></div>
              <div className="stat-content">
                <h3>Data Fetched from Tally</h3>
                <div className="stat-number">{loading ? "Loading..." : totalFetched.toLocaleString()}</div>
                <div className="stat-change positive">↗ Live Data</div>
              </div>
              <div className="stat-chart">
                <svg width="100" height="40" viewBox="0 0 100 40">
                  <path d="M5,35 Q25,20 45,25 T85,15" stroke="#4F46E5" strokeWidth="2" fill="none" />
                </svg>
              </div>
            </div>

            <div className="stat-card orange">
              <div className="stat-icon"><BarChart3 size={24} /></div>
              <div className="stat-content">
                <h3>Data Migrated to Zoho Books</h3>
                <div className="stat-number">0</div>
                <div className="stat-change positive">↗ Pending sync</div>
              </div>
              <div className="stat-chart">
                <svg width="100" height="40" viewBox="0 0 100 40">
                  <path d="M5,35 Q25,30 45,20 T85,15" stroke="#F59E0B" strokeWidth="2" fill="none" />
                </svg>
              </div>
            </div>

            <div className="stat-card yellow1">
              <div className="stat-content">
                <h3 style={{ fontWeight: 'bold', fontSize: '18px' }}>Sync Your Data in One Place</h3>
                <p>The sync process for transactions in Tally2Books keeps data updated across the system.</p>
              </div>
              <div className="sync-button-container">
                <button className="sync-button" onClick={fetchTransactions}>Refresh</button>
              </div>
            </div>
          </div>

          {/* Breakdown */}
          <div style={{ display: 'flex', gap: '12px', margin: '12px 0', flexWrap: 'wrap' }}>
            {[
              { label: 'Invoices', value: counts.invoices, color: '#8B5CF6' },
              { label: 'Receipts', value: counts.receipts, color: '#EF4444' },
            ].map(item => (
              <div key={item.label} style={{
                background: 'white', border: `2px solid ${item.color}`,
                borderRadius: '8px', padding: '12px 20px', textAlign: 'center', minWidth: '100px'
              }}>
                <div style={{ fontSize: '22px', fontWeight: '700', color: item.color }}>{item.value}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>{item.label}</div>
              </div>
            ))}
          </div>

          {/* Activities Table */}
          <div className="content-grid-dashboard" style={{ display: "grid", gridTemplateColumns: "1fr" }}>
            <div className="content-card">
              <h3>Recent Activities</h3>
              <div className="table-container">
                <table className="activities-table">
                  <thead>
                    <tr>
                      <th>S.No</th>
                      <th>Type</th>
                      <th>Customer Name</th>
                      <th>Amount</th>
                      <th>Status</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activities.slice(0, 50).map((activity) => (
                      <tr key={activity.sNo}>
                        <td>{activity.sNo}</td>
                        <td>{activity.type}</td>
                        <td>{activity.name}</td>
                        <td>₹{activity.amount}</td>
                        <td>
                          <span className={`status ${activity.status.toLowerCase()}`}>
                            {activity.status}
                          </span>
                        </td>
                        <td>{activity.lastMigrated}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!loading && activities.length === 0 && (
                  <div className="no-data">
                    <div className="no-data-icon">📊</div>
                    <p>No data yet — run the Sync Agent to fetch transactions from Tally</p>
                  </div>
                )}
                {loading && (
                  <div className="no-data">
                    <p>Loading...</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Transactions;