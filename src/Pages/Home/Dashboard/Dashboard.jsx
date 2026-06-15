import React, { useState, useEffect } from 'react';
import { Bell, User, BarChart3, CreditCard, Database } from 'lucide-react';
import './Dashboard.css';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../../../components/Sidebar';

const Dashboard = () => {
  const navigate = useNavigate();

  // User data state
  const [userData, setUserData] = useState({
    name: localStorage.getItem("userName") ||
      JSON.parse(localStorage.getItem("userData") || '{}')?.name ||
      "User",
    loading: false
  });

  // Dashboard data states
  const [dashboardData, setDashboardData] = useState({
    fetched_from_tally: 0,
    migrated_to_zoho: 0,
    pending_migration_to_zoho: 0,
    customers: 0,
    vendors: 0,
    COA: 0,
    items: 0,
    invoices: 0,
    receipts: 0,
    loading: true
  });

  // Snackbar alert states
  const [snackbarAlert, setSnackbarAlert] = useState({
    show: false,
    type: '',
    message: ''
  });

  // Track if initial load is complete to avoid repeated success messages
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);

  // Function to fetch user data
  const fetchUserData = async () => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) return;

      const response = await fetch('https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/me/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`  // hits localhost Django
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUserData({
          name: data.first_name && data.last_name
            ? `${data.first_name} ${data.last_name}`
            : data.username || data.email || 'User',
          loading: false
        });
      } else {
        setUserData(prev => ({ ...prev, loading: false }));
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
      setUserData(prev => ({ ...prev, loading: false }));
    }
  };

  // Fetch dashboard data on component mount and set up interval
  useEffect(() => {
    console.log("Dashboard component mounted, starting data fetch...");

    // Check for authentication token first
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
      console.log("No auth token found, redirecting to login...");

      return;
    }

    // Initial fetch when component mounts
    fetchDashboardData();

    // Set up interval to fetch data every 30 seconds
    const intervalId = setInterval(() => {
      console.log("Dashboard interval triggered, fetching data...");
      // Check auth token before each fetch
      const currentToken = localStorage.getItem('authToken');
      if (!currentToken) {
        console.log("Auth token missing during interval, redirecting to login...");
        clearInterval(intervalId);
        navigate('/signin');
        return;
      }
      fetchDashboardData();
    }, 30000); // 30 seconds

    // Cleanup interval on component unmount
    return () => {
      console.log("Dashboard component unmounting, clearing interval...");
      clearInterval(intervalId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate]); // Add navigate to dependency array

  // Simplified function to fetch dashboard data from the correct endpoint
  const fetchDashboardData = async () => {
    try {
      console.log("Starting fetchDashboardData...");

      const authToken = localStorage.getItem('authToken');
      console.log("Auth token:", authToken ? "Present" : "Missing");

      if (!authToken) {
        console.log("No auth token found, redirecting to login...");
        navigate('/signin');
        throw new Error('Authentication token not found. Please login again.');
      }

      // Use the correct endpoint that matches your API structure
      const endpoint = 'http://127.0.0.1:8000/api/data-migration-status/';

      console.log(`Fetching from endpoint: ${endpoint}`);

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`  // ✅ Bearer not Token
        }
      });

      console.log(`Response status: ${response.status}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Dashboard response error:", errorText);

        // Handle authentication errors specifically
        if (response.status === 401 || response.status === 403) {
          console.log("Authentication failed, clearing token and redirecting to login...");
          sessionStorage.removeItem('authToken');
          navigate('/signin');
          throw new Error('Session expired. Please login again.');
        }

        throw new Error(`Failed to fetch dashboard data: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log("Raw dashboard API response:", data);

      // Since the API response structure matches exactly what we need, use it directly
      setDashboardData({
        fetched_from_tally: data.fetched_from_tally || 0,
        migrated_to_zoho: data.migrated_to_zoho || 0,
        pending_migration_to_zoho: data.pending_migration_to_zoho || 0,
        customers: data.customers || 0,
        vendors: data.vendors || 0,
        COA: data.COA || 0,
        items: data.items || 0,
        invoices: data.invoices || 0,
        receipts: data.receipts || 0,
        loading: false
      });

      console.log("Dashboard data updated successfully");

      // Clear any previous error alerts on successful fetch
      hideSnackbarAlert();

      // Show success message only on initial load
      if (!initialLoadComplete) {
        showSnackbarAlert('success', '✅ Dashboard data loaded successfully');
        setInitialLoadComplete(true);
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error);

      // Handle authentication errors
      if (error.message.includes('Session expired') || error.message.includes('Authentication')) {
        return; // Don't show error alert, already redirecting
      }

      // Show error alert
      showSnackbarAlert('error', `Failed to load dashboard data: ${error.message}`);

      // Set loading to false even on error but keep previous data
      setDashboardData(prev => ({
        ...prev,
        loading: false
      }));
    }
  };

  const showSnackbarAlert = (type, message) => {
    setSnackbarAlert({
      show: true,
      type: type,
      message: message
    });
  };

  // Function to hide snackbar alert
  const hideSnackbarAlert = () => {
    setSnackbarAlert({
      show: false,
      type: '',
      message: ''
    });
  };

  // Calculate analytics data - Masters for bar chart, Transactions for donut chart
  const calculateMastersData = () => {
    const totalMasters = dashboardData.customers + dashboardData.vendors + dashboardData.COA + dashboardData.items;

    if (totalMasters === 0) return [];

    return [
      { name: 'Customers', value: dashboardData.customers, percentage: ((dashboardData.customers / totalMasters) * 100).toFixed(1), color: '#3B82F6' },
      { name: 'Vendors', value: dashboardData.vendors, percentage: ((dashboardData.vendors / totalMasters) * 100).toFixed(1), color: '#10B981' },
      { name: 'Chart of Accounts', value: dashboardData.COA, percentage: ((dashboardData.COA / totalMasters) * 100).toFixed(1), color: '#6B7280' },
      { name: 'Items', value: dashboardData.items, percentage: ((dashboardData.items / totalMasters) * 100).toFixed(1), color: '#F59E0B' }
    ];
  };

  const calculateTransactionsData = () => {
    const totalTransactions = dashboardData.invoices + dashboardData.receipts;

    if (totalTransactions === 0) return [];

    return [
      { name: 'Invoices', value: dashboardData.invoices, percentage: ((dashboardData.invoices / totalTransactions) * 100).toFixed(1), color: '#8B5CF6' },
      { name: 'Receipts', value: dashboardData.receipts, percentage: ((dashboardData.receipts / totalTransactions) * 100).toFixed(1), color: '#EF4444' }
    ];
  };

  const mastersData = calculateMastersData();
  const transactionsData = calculateTransactionsData();
  const totalTransactions = dashboardData.invoices + dashboardData.receipts;
  const totalMasters = dashboardData.customers + dashboardData.vendors + dashboardData.COA + dashboardData.items;

  return (
    <div className="dashboard-page">
      {/* Add required styles for animations */}
      <style jsx>{`
        @keyframes shimmer {
          0% { left: -100%; }
          100% { left: 100%; }
        }
        
        @keyframes fadeIn {
          0% { opacity: 0; transform: translateY(10px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
        
        .progress-bar-fill.syncing {
          background: linear-gradient(90deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%);
          position: relative;
          overflow: hidden;
        }
        
        .progress-bar-fill.syncing::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
          animation: shimmer 1.5s infinite;
        }
        
        .api-status {
          position: absolute;
          top: 16px;
          right: 16px;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #10b981;
          box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
        }
        
        .api-status.disconnected {
          background: #ef4444;
          box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
          animation: blink 1s infinite;
        }
      `}</style>

      <div className="dashboard-container">
        {/* Sidebar */}
        <Sidebar />

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
                <span>{JSON.parse(localStorage.getItem("userData") || '{}')?.name || localStorage.getItem("userName") || "User"}</span>
              </div>
            </div>
          </div>

          {/* Debug Section - Remove this in production */}
          {/* <div className="debug-section" style={{ 
            background: '#f8f9fa', 
            border: '1px solid #dee2e6', 
            borderRadius: '8px', 
            padding: '16px', 
            margin: '16px 0',
            fontSize: '14px',
            fontFamily: 'monospace'
          }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>🔧 Debug Information</h4>
            <div><strong>Auth Token:</strong> {sessionStorage.getItem('authToken') ? 'Present' : 'Missing'}</div>
            <div><strong>Endpoint:</strong> api/data-migration-status/</div>
            <div><strong>Current Data:</strong></div>
            <pre style={{ background: '#e9ecef', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
              {JSON.stringify(dashboardData, null, 2)}
            </pre>
            <button 
              onClick={fetchDashboardData}
              style={{
                background: '#007bff',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                fontSize: '12px',
                cursor: 'pointer',
                marginTop: '8px'
              }}
            >
              🔄 Refresh Data
            </button>
          </div> */}

          {/* Snackbar Alert */}
          {snackbarAlert.show && (
            <div className={`snackbar-alert ${snackbarAlert.type}`}>
              <div className="snackbar-content">
                <div className="snackbar-icon">
                  {snackbarAlert.type === 'error' ? '' :
                    snackbarAlert.type === 'success' ? '' :
                      snackbarAlert.type === 'warning' ? '' : 'ℹ'}
                </div>
                <div className="snackbar-message">
                  {snackbarAlert.message.split('\n').map((line, index) => (
                    <div key={index} className="snackbar-line">{line}</div>
                  ))}
                </div>
                <button className="snackbar-close" onClick={hideSnackbarAlert}>×</button>
              </div>
            </div>
          )}

          {/* Stats Cards with Real Data */}
          <div className="stats-grid">
            <div className="stat-card blue">
              <div className="stat-icon">
                <Database size={24} />
              </div>
              <div className="stat-content">
                <h3>Data Fetched from Tally</h3>
                <div className="stat-number">
                  {dashboardData.loading ? "Loading..." : dashboardData.fetched_from_tally.toLocaleString()}
                  {dashboardData.loading && <span className="loading-spinner">⟳</span>}
                </div>
                <div className="stat-change positive">↗ Live Data</div>
              </div>
              <div className="stat-chart">
                <svg width="100" height="40" viewBox="0 0 100 40">
                  <path d="M5,35 Q25,20 45,25 T85,15" stroke="#4F46E5" strokeWidth="2" fill="none" />
                </svg>
              </div>
            </div>

            <div className="stat-card orange">
              <div className="stat-icon">
                <BarChart3 size={24} />
              </div>
              <div className="stat-content">
                <h3>Data Migrated to Zoho Books</h3>
                <div className="stat-number">
                  {dashboardData.loading ? "Loading..." : dashboardData.migrated_to_zoho.toLocaleString()}
                  {dashboardData.loading && <span className="loading-spinner">⟳</span>}
                </div>
                <div className="stat-change positive">↗ Live Data</div>
              </div>
              <div className="stat-chart">
                <svg width="100" height="40" viewBox="0 0 100 40">
                  <path d="M5,35 Q25,30 45,20 T85,15" stroke="#F59E0B" strokeWidth="2" fill="none" />
                </svg>
              </div>
            </div>

            <div className="stat-card yellow">
              <div className="stat-icon">
                <CreditCard size={24} />
              </div>
              <div className="stat-content">
                <h3>Pending Migration</h3>
                <div className="stat-number">
                  {dashboardData.loading ? "Loading..." : dashboardData.pending_migration_to_zoho.toLocaleString()}
                  {dashboardData.loading && <span className="loading-spinner">⟳</span>}
                </div>
                <div className="stat-change neutral">Live Data</div>
              </div>
              <div className="stat-chart">
                <svg width="100" height="40" viewBox="0 0 100 40">
                  <path d="M5,35 Q25,25 45,30 T85,20" stroke="#EAB308" strokeWidth="2" fill="none" />
                </svg>
              </div>
            </div>
          </div>

          {/* Content Grid */}
          <div className="content-grid-dashboard">
            {/* Masters Bar Chart */}
            <div className="content-card">
              <h3>Masters</h3>
              <div className="masters-chart-container">
                {dashboardData.loading ? (
                  <div className="loading-state">
                    <div className="loading-spinner">⟳</div>
                    <p>Loading masters data...</p>
                  </div>
                ) : (
                  <div className="bar-chart">
                    <div className="chart-bars">
                      {mastersData.map((item, index) => (
                        <div key={item.name} className="bar-item">
                          <div className="bar-container">
                            <div
                              className={`bar ${item.name.toLowerCase().replace(/\s+/g, '-')}-bar`}
                              style={{
                                height: `${Math.max((item.value / Math.max(totalMasters, 1)) * 100, 5)}%`,
                                backgroundColor: item.color
                              }}
                            >
                              <div className="bar-tooltip">
                                <span className="tooltip-value">{item.value}</span>
                                <span className="tooltip-percentage">{item.percentage}%</span>
                              </div>
                            </div>
                          </div>
                          <span className="bar-label">{item.name}</span>
                        </div>
                      ))}
                    </div>

                    {/* Masters Summary */}
                    <div className="chart-summary" style={{ marginTop: '20px', padding: '12px', background: '#f8f9fa', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '14px', color: '#6b7280' }}>Total Masters:</span>
                        <span style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>{totalMasters}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Transactions Donut Chart */}
            <div className="content-card analytics">
              <h3>Transactions</h3>
              <div className="analytics-chart">
                <div className="donut-chart">
                  {dashboardData.loading ? (
                    <div className="loading-state">
                      <div className="loading-spinner">⟳</div>
                      <p>Loading transactions...</p>
                    </div>
                  ) : totalTransactions === 0 ? (
                    <div className="donut-chart">
                      {dashboardData.loading ? (
                        <div className="loading-state">
                          <div className="loading-spinner">⟳</div>
                          <p>Loading transactions...</p>
                        </div>
                      ) : (
                        <>
                          <svg width="160" height="160" viewBox="0 0 160 160">
                            {/* Always show base gray ring */}
                            <circle
                              cx="80"
                              cy="80"
                              r="60"
                              fill="none"
                              stroke="#D1D5DB"
                              strokeWidth="20"
                            />

                            {/* Show colored segments only if data exists */}
                            {totalTransactions > 0 && transactionsData.map((item, index) => {
                              const totalValue = transactionsData.reduce((sum, d) => sum + d.value, 0);
                              const percentage = (item.value / totalValue) * 100;
                              const circumference = 2 * Math.PI * 60;
                              const strokeDasharray = circumference;
                              const strokeDashoffset = circumference - (circumference * percentage) / 100;
                              const rotation = transactionsData.slice(0, index).reduce((sum, d) => {
                                const prevPercentage = (d.value / totalValue) * 100;
                                return sum + (prevPercentage * 3.6);
                              }, -90);

                              return (
                                <circle
                                  key={item.name}
                                  cx="80"
                                  cy="80"
                                  r="60"
                                  fill="none"
                                  stroke={item.color}
                                  strokeWidth="20"
                                  strokeDasharray={strokeDasharray}
                                  strokeDashoffset={strokeDashoffset}
                                  transform={`rotate(${rotation} 80 80)`}
                                  style={{ transition: 'all 0.3s ease' }}
                                />
                              );
                            })}
                          </svg>

                          {/* Center Label */}
                          <div className="chart-center">
                            {totalTransactions > 0 ? (
                              <>
                                <div className="chart-percentage" style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937' }}>
                                  {totalTransactions}
                                </div>
                                <div className="chart-label" style={{ fontSize: '12px', color: '#6b7280' }}>Total</div>
                              </>
                            ) : (
                              <>
                                <div className="chart-percentage" style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280', fontStyle: 'italic' }}>
                                  No data
                                </div>
                                <div className="chart-label" style={{ fontSize: '12px', color: '#9CA3AF' }}>Transactions</div>
                              </>
                            )}
                          </div>
                        </>
                      )}
                    </div>

                  ) : (
                    <>
                      <svg width="160" height="160" viewBox="0 0 160 160">
                        <circle cx="80" cy="80" r="60" fill="none" stroke="#E5E7EB" strokeWidth="20" />
                        {transactionsData.map((item, index) => {
                          const totalValue = transactionsData.reduce((sum, d) => sum + d.value, 0);
                          const percentage = totalValue > 0 ? (item.value / totalValue) * 100 : 0;
                          const circumference = 2 * Math.PI * 60;
                          const strokeDasharray = circumference;
                          const strokeDashoffset = circumference - (circumference * percentage) / 100;
                          const rotation = transactionsData.slice(0, index).reduce((sum, d) => {
                            const prevPercentage = totalValue > 0 ? (d.value / totalValue) * 100 : 0;
                            return sum + (prevPercentage * 3.6);
                          }, -90);

                          return (
                            <circle
                              key={item.name}
                              cx="80"
                              cy="80"
                              r="60"
                              fill="none"
                              stroke={item.color}
                              strokeWidth="20"
                              strokeDasharray={strokeDasharray}
                              strokeDashoffset={strokeDashoffset}
                              transform={`rotate(${rotation} 80 80)`}
                              style={{ transition: 'all 0.3s ease' }}
                            />
                          );
                        })}
                      </svg>
                      <div className="chart-center">
                        <div className="chart-percentage" style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937' }}>
                          {totalTransactions}
                        </div>
                        <div className="chart-label" style={{ fontSize: '12px', color: '#6b7280' }}>Total</div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <div className="analytics-legend">
                {transactionsData.map((item) => (
                  <div key={item.name} className="legend-item">
                    <div className="legend-color" style={{ backgroundColor: item.color }}></div>
                    <span>{item.name} ({item.value})</span>
                  </div>
                ))}
                {totalTransactions === 0 && (
                  <div className="legend-item" style={{ color: '#6b7280', fontStyle: 'italic' }}>
                    <div className="legend-color" style={{ backgroundColor: '#e5e7eb' }}></div>
                    <span>No transactions yet</span>
                  </div>
                )}
              </div>


            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
