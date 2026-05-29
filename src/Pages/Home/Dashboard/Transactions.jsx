import React from 'react';
import { Bell, User, BarChart3, Database } from 'lucide-react';
import './Dashboard.css';
import Sidebar from '../../../components/Sidebar';


  const recentActivities = [
    { sNo: 1, type: 'Customer', customerName: 'John Doe', status: 'Completed', lastMigrated: '2024-01-15' },
    { sNo: 2, type: 'Vendor', customerName: 'ABC Corp', status: 'In Progress', lastMigrated: '2024-01-14' },
    { sNo: 3, type: 'Item', customerName: 'Product X', status: 'Pending', lastMigrated: '2024-01-13' }
  ];
function Transactions() {
  return (
       <div className="dashboard-page">
    <div className="dashboard-container">
      {/* Sidebar */}
      
        <Sidebar />

       

     
      {/* Main Content */}
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

          <div className="stat-card yellow1">
 
             
           
            <div className="stat-content">
      <h3 style={{ fontWeight: 'bold', fontSize: '18px' }}>Sync Your Data in One Place</h3>

              <h3>The sync process for customer fields in Tally2 Books keeps master data updated across the system.</h3>

            </div>
            <div className="sync-button-container">
             <button className="sync-button">Sync Now</button>
            </div>
          </div>
        </div>

        {/* Content Grid */}
      <div className="content-grid-dashboard" style={{ display: "grid", gridTemplateColumns: "1fr" }}>
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


        
        </div>
      </div>
    </div>
    
 
    </div>
    
  );
}

export default Transactions;
