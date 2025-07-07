import React, { useState } from 'react';
import { Bell, User, Settings, HelpCircle, Phone, BarChart3, Users, CreditCard, Database, Grid3x3 } from 'lucide-react';
import './Dashboard.css';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('Dashboard');

  const sidebarItems = [
    { id: 'Dashboard', icon: Grid3x3, label: 'Dashboard', active: true },
    { id: 'Masters', icon: Users, label: 'Masters' },
    { id: 'Transactions', icon: CreditCard, label: 'Transactions' },
    { id: 'Settings', icon: Settings, label: 'Settings' }
  ];

  const supportItems = [
    { id: 'Help', icon: HelpCircle, label: 'Help Center' },
    { id: 'Contact', icon: Phone, label: 'Contact Support' }
  ];

  const recentActivities = [
    { sNo: 1, type: 'Customer', customerName: 'John Doe', status: 'Completed', lastMigrated: '2024-01-15' },
    { sNo: 2, type: 'Vendor', customerName: 'ABC Corp', status: 'In Progress', lastMigrated: '2024-01-14' },
    { sNo: 3, type: 'Item', customerName: 'Product X', status: 'Pending', lastMigrated: '2024-01-13' }
  ];

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h2 className="logo">Tally2Books</h2>
        </div>
        
        <nav className="sidebar-nav">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-support">
          <h3>Support</h3>
          {supportItems.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} className="nav-item">
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        <div className="sidebar-upgrade">
          <div className="upgrade-icon">
            <div className="triangle"></div>
          </div>
          <button className="upgrade-btn">Upgrade Now</button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Header */}
        <div className="header">
          <div className="header-left">
            <h1>Dashboard</h1>
            <p>Monitor and manage your entire data migration process from a single dashboard</p>
          </div>
          <div className="header-right">
            <Bell className="notification-icon" />
            <div className="user-profile">
              <User className="user-icon" />
              <span>John Andrew</span>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card blue">
            <div className="stat-icon">
              <Database size={24} />
            </div>
            <div className="stat-content">
              <h3>Data Fetched from Tally</h3>
              <div className="stat-number">24,500</div>
              <div className="stat-change positive">↗ 2.5%</div>
            </div>
            <div className="stat-chart">
              <svg width="100" height="40" viewBox="0 0 100 40">
                <path d="M5,35 Q25,20 45,25 T85,15" stroke="#4F46E5" strokeWidth="2" fill="none"/>
              </svg>
            </div>
          </div>

          <div className="stat-card orange">
            <div className="stat-icon">
              <BarChart3 size={24} />
            </div>
            <div className="stat-content">
              <h3>Data Migrated to Zoho Books</h3>
              <div className="stat-number">24,500</div>
              <div className="stat-change positive">↗ 2.5%</div>
            </div>
            <div className="stat-chart">
              <svg width="100" height="40" viewBox="0 0 100 40">
                <path d="M5,35 Q25,30 45,20 T85,15" stroke="#F59E0B" strokeWidth="2" fill="none"/>
              </svg>
            </div>
          </div>

          <div className="stat-card yellow">
            <div className="stat-icon">
              <CreditCard size={24} />
            </div>
            <div className="stat-content">
              <h3>Pending Migration</h3>
              <div className="stat-number">7,500</div>
            </div>
            <div className="stat-chart">
              <svg width="100" height="40" viewBox="0 0 100 40">
                <path d="M5,35 Q25,25 45,30 T85,20" stroke="#EAB308" strokeWidth="2" fill="none"/>
              </svg>
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="content-grid-dashboard ">
          {/* Recent Activities */}
          <div className="content-card">
            <h3>Recent Activities</h3>
            <div className="table-container">
              <table className="activities-table">
                <thead>
                  <tr>
                    <th>S.No</th>
                    <th>Type</th>
                    <th>Customer Name</th>
                    <th>Status</th>
                    <th>Last Migrated Data</th>
                  </tr>
                </thead>
                <tbody>
                  {recentActivities.map((activity) => (
                    <tr key={activity.sNo}>
                      <td>{activity.sNo}</td>
                      <td>{activity.type}</td>
                      <td>{activity.customerName}</td>
                      <td>
                        <span className={`status ${activity.status.toLowerCase().replace(' ', '-')}`}>
                          {activity.status}
                        </span>
                      </td>
                      <td>{activity.lastMigrated}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {recentActivities.length === 0 && (
                <div className="no-data">
                  <div className="no-data-icon">📊</div>
                  <p>No Data Found: Manage Migration from One Dashboard</p>
                </div>
              )}
            </div>
          </div>

          {/* Analytics */}
          <div className="content-card analytics">
            <h3>Analytics</h3>
            <div className="analytics-chart">
              <div className="donut-chart">
                <svg width="160" height="160" viewBox="0 0 160 160">
                  <circle cx="80" cy="80" r="60" fill="none" stroke="#E5E7EB" strokeWidth="20"/>
                  <circle cx="80" cy="80" r="60" fill="none" stroke="#3B82F6" strokeWidth="20" 
                          strokeDasharray="301.6" strokeDashoffset="60.32" transform="rotate(-90 80 80)"/>
                  <circle cx="80" cy="80" r="60" fill="none" stroke="#10B981" strokeWidth="20" 
                          strokeDasharray="301.6" strokeDashoffset="180.96" transform="rotate(108 80 80)"/>
                  <circle cx="80" cy="80" r="60" fill="none" stroke="#F59E0B" strokeWidth="20" 
                          strokeDasharray="301.6" strokeDashoffset="240.32" transform="rotate(180 80 80)"/>
                  <circle cx="80" cy="80" r="60" fill="none" stroke="#EF4444" strokeWidth="20" 
                          strokeDasharray="301.6" strokeDashoffset="271.44" transform="rotate(252 80 80)"/>
                  <circle cx="80" cy="80" r="60" fill="none" stroke="#6366F1" strokeWidth="20" 
                          strokeDasharray="301.6" strokeDashoffset="286.52" transform="rotate(288 80 80)"/>
                </svg>
                <div className="chart-center">
                  <div className="chart-percentage">80%</div>
                  <div className="chart-label">Transactions</div>
                </div>
              </div>
            </div>
            <div className="analytics-legend">
              <div className="legend-item">
                <div className="legend-color blue"></div>
                <span>Customer</span>
              </div>
              <div className="legend-item">
                <div className="legend-color green"></div>
                <span>Vendors</span>
              </div>
              <div className="legend-item">
                <div className="legend-color gray"></div>
                <span>Items</span>
              </div>
              <div className="legend-item">
                <div className="legend-color orange"></div>
                <span>Transactions</span>
              </div>
              <div className="legend-item">
                <div className="legend-color yellow"></div>
                <span>Chart of Accounts</span>
              </div>
            </div>

            <div className="migration-health">
              <h4>Migration Health</h4>
              <div className="health-chart">
                <div className="health-percentage">80%</div>
                <div className="health-label">Transactions</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;