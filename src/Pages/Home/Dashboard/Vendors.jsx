import React, { useState, useEffect } from 'react';
import { Bell, User, BarChart3, CreditCard, Database } from 'lucide-react';
import './Dashboard.css';
import Sidebar from '../../../components/Sidebar';

function Customers() {
  const [dashboardData, setDashboardData] = useState({
    dataFetchedFromTally: 0,
    dataMigratedToZoho: 0,
    pendingMigration: 0,
    loading: true
  });
  
  const [recentActivities, setRecentActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Snackbar alert states
  const [snackbarAlert, setSnackbarAlert] = useState({
    show: false,
    type: '',
    message: ''
  });

  // Get auth token from sessionStorage
  const getAuthToken = () => {
    return sessionStorage.getItem('authToken');
  };

  // Function to show snackbar alert
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

  // Single API call to fetch all dashboard data
  const fetchAllDashboardData = async () => {
    try {
      console.log("Starting fetchAllDashboardData...");
      
      const authToken = getAuthToken();
      console.log("Auth token:", authToken ? "Present" : "Missing");
      
      if (!authToken) {
        throw new Error('Authentication token not found. Please login again.');
      }

      // Updated API endpoint
      const endpoint = `https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/vendordashboard/`;
      
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`
        }
      });

      console.log("Complete dashboard response status:", response.status);
      console.log("Complete dashboard response ok:", response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Complete dashboard response error:", errorText);
        throw new Error(`Failed to fetch dashboard data: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log("Complete dashboard raw API response:", data);
      
      // Update dashboard statistics from summary data
      setDashboardData({
        dataFetchedFromTally: data.summary?.fetched_from_tally || 0,
        dataMigratedToZoho: data.summary?.pushed_to_zoho || 0,
        pendingMigration: data.summary?.pending_to_push_to_zoho || 0,
        loading: false
      });

      // Transform recent activities data from all_ledgers
      const activitiesData = data.all_ledgers || [];
      const transformedActivities = activitiesData.map((contact, index) => ({
        sNo: index + 1,
        name: contact.name || 'N/A',
        parent: contact.parent || 'N/A',
        email: contact.email || 'N/A',
        website: contact.website || 'N/A',
        mobile: contact.ledger_mobile || 'N/A',
        state: contact.state_name || 'N/A',
        pincode: contact.pincode || 'N/A',
        country: contact.country_name || 'N/A',
        status: contact.pushed_to_zoho ? 'Completed' : 'Pending'
      }));

      console.log("Processed recent activities data:", transformedActivities);
      setRecentActivities(transformedActivities);
      setIsLoading(false);

      // Clear any previous error alerts on successful fetch
      hideSnackbarAlert();

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      
      // Show error alert with detailed message
      showSnackbarAlert('error', `Failed to load dashboard data: ${error.message}`);

      // Set loading to false even on error but keep previous data
      setDashboardData(prev => ({ ...prev, loading: false }));
      setIsLoading(false);
    }
  };

  // Fetch all data on component mount and set up interval
  useEffect(() => {
    console.log("Component mounted, starting data fetch...");
    
    // Initial fetch when component mounts
    fetchAllDashboardData();
    
    // Set up interval to fetch data every 10 seconds
    const intervalId = setInterval(() => {
      console.log("Interval triggered, fetching data...");
      fetchAllDashboardData();
    }, 10000); // 10 seconds = 10000 milliseconds

    // Cleanup interval on component unmount
    return () => {
      console.log("Component unmounting, clearing interval...");
      clearInterval(intervalId);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array means this runs once on mount

  // Refresh data function
  const refreshData = () => {
    setDashboardData(prev => ({ ...prev, loading: true }));
    setIsLoading(true);
    hideSnackbarAlert(); // Clear any previous alerts
    fetchAllDashboardData();
  };

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
              <h1>Vendors</h1>
              <p>Monitor and manage your entire data migration process from a single dashboard</p>
            </div>
            <div className="header-right">
              <button onClick={refreshData} className="refresh-btn" title="Refresh Data">
                🔄
              </button>
              <Bell className="notification-icon" />
              <div className="user-profile">
                <User className="user-icon" />
                <span>{JSON.parse(localStorage.getItem("userData") || '{}')?.name || localStorage.getItem("userName") || "User"}</span>
              </div>
            </div>
          </div>

          {/* Snackbar Alert */}
          {snackbarAlert.show && (
            <div className={`snackbar-alert ${snackbarAlert.type}`}>
              <div className="snackbar-content">
                <div className="snackbar-icon">
                  {snackbarAlert.type === 'error' ? '❌' : 
                   snackbarAlert.type === 'success' ? '✅' : 
                   snackbarAlert.type === 'warning' ? '⚠️' : 'ℹ️'}
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

          {/* Debug Info - Remove this in production */}
          <div style={{ background: '#f0f0f0', padding: '10px', margin: '10px 0', fontSize: '12px' }}>
            <strong>Debug Info:</strong><br/>
            Overall Loading: {isLoading.toString()}<br/>
            Dashboard Stats Loading: {dashboardData.loading.toString()}<br/>
            Data Fetched from Tally: {dashboardData.dataFetchedFromTally}<br/>
            Data Migrated to Zoho: {dashboardData.dataMigratedToZoho}<br/>
            Pending Migration: {dashboardData.pendingMigration}<br/>
            Recent Activities Count: {recentActivities.length}<br/>
            Auth Token: {getAuthToken() ? 'Present' : 'Missing'}
          </div>

          {/* Stats Cards */}
          <div className="stats-grid">
            <div className="stat-card blue">
              <div className="stat-icon">
                <Database size={24} />
              </div>
              <div className="stat-content">
                <h3>Data Fetched from Tally</h3>
                <div className="stat-number">
                  {dashboardData.loading ? "Loading..." : dashboardData.dataFetchedFromTally.toLocaleString()}
                  {dashboardData.loading && <span className="loading-spinner">⟳</span>}
                </div>
                <div className="stat-change positive">↗ Live Data</div>
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
                <div className="stat-number">
                  {dashboardData.loading ? "Loading..." : dashboardData.dataMigratedToZoho.toLocaleString()}
                  {dashboardData.loading && <span className="loading-spinner">⟳</span>}
                </div>
                <div className="stat-change positive">↗ Live Data</div>
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
                <div className="stat-number">
                  {dashboardData.loading ? "Loading..." : dashboardData.pendingMigration.toLocaleString()}
                  {dashboardData.loading && <span className="loading-spinner">⟳</span>}
                </div>
                <div className="stat-change neutral">Live Data</div>
              </div>
              <div className="stat-chart">
                <svg width="100" height="40" viewBox="0 0 100 40">
                  <path d="M5,35 Q25,25 45,30 T85,20" stroke="#EAB308" strokeWidth="2" fill="none"/>
                </svg>
              </div>
            </div>
          </div>

          {/* Content Grid */}
          <div className="content-grid-dashboard" style={{ display: "grid", gridTemplateColumns: "1fr" }}>
            {/* Recent Activities */}
            <div className="content-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>Recent Activities</h3>
                {isLoading && <span className="loading-spinner">⟳ Loading...</span>}
              </div>
              
              <div className="table-container">
                <table className="activities-table">
                  <thead>
                    <tr>
                      <th>S.No</th>
                      <th>Name</th>
                      <th>Parent</th>
                      <th>Email</th>
                      <th>Website</th>
                      <th>Mobile</th>
                      <th>State</th>
                      <th>Pincode</th>
                      <th>Country</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentActivities.length > 0 ? (
                      recentActivities.map((activity) => (
                        <tr key={activity.sNo}>
                          <td>{activity.sNo}</td>
                          <td>{activity.name}</td>
                          <td>{activity.parent}</td>
                          <td>{activity.email}</td>
                          <td>{activity.website}</td>
                          <td>{activity.mobile}</td>
                          <td>{activity.state}</td>
                          <td>{activity.pincode}</td>
                          <td>{activity.country}</td>
                          <td>
                            <span className={`status ${activity.status.toLowerCase().replace(' ', '-')}`}>
                              {activity.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="10" style={{ textAlign: 'center', padding: '40px' }}>
                          {isLoading ? (
                            <div>Loading activities...</div>
                          ) : (
                            <div className="no-data">
                              <div className="no-data-icon">📊</div>
                              <p>No Data Found: Manage Migration from One Dashboard</p>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Customers;
