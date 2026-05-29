import React, { useState, useEffect } from 'react';
import { Bell, User, BarChart3, CreditCard, Package } from 'lucide-react';
import './Dashboard.css';
import Sidebar from '../../../components/Sidebar';

function ItemsDashboard() {
  const [dashboardData, setDashboardData] = useState({
    dataFetchedFromTally: 0,
    dataMigratedToZoho: 0,
    pendingMigration: 0,
    loading: true
  });
  
  const [itemsData, setItemsData] = useState([]);
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
      console.log("Starting fetchAllDashboardData for Items...");
      
      const authToken = getAuthToken();
      console.log("Auth token:", authToken ? "Present" : "Missing");
      
      if (!authToken) {
        throw new Error('Authentication token not found. Please login again.');
      }

      // Items API endpoint
      const endpoint = `https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/itemsdashboard/`;
      
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`
        }
      });

      console.log("Items dashboard response status:", response.status);
      console.log("Items dashboard response ok:", response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Items dashboard response error:", errorText);
        throw new Error(`Failed to fetch Items dashboard data: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log("Items dashboard raw API response:", data);
      console.log("API Response Keys:", Object.keys(data));
      
      // Log the first few items to see structure
      const itemsApiData = data.all_items || data.items || data.all_ledgers || [];
      console.log("Items array length:", itemsApiData.length);
      if (itemsApiData.length > 0) {
        console.log("First item structure:", itemsApiData[0]);
        console.log("First item keys:", Object.keys(itemsApiData[0]));
      }
      
      // Update dashboard statistics from summary data
      setDashboardData({
        dataFetchedFromTally: data.summary?.fetched_from_tally || 0,
        dataMigratedToZoho: data.summary?.pushed_to_zoho || 0,
        pendingMigration: (data.summary?.fetched_from_tally || 0) - (data.summary?.pushed_to_zoho || 0),
        loading: false
      });

      // Transform items data with extensive field mapping
      const transformedItems = itemsApiData.map((item, index) => {
        console.log(`Item ${index + 1} raw data:`, item);
        return {
          sNo: index + 1,
          name: item.name || item.item_name || item.product_name || 'N/A',
          rate: item.rate || item.price || item.unit_price || item.selling_price || item.amount || 'N/A',
          description: item.description || item.desc || item.details || 'N/A',
          sku: item.sku || item.item_code || item.product_code || item.code || 'N/A',
          product_type: item.product_type || item.type || item.category || item.item_type || 'N/A',
          account: item.account || item.account_name || item.ledger || item.ledger_name || 'N/A',
          gst_rate: item.gst_rate || item.tax_rate || item.gst || item.tax || item.tax_percentage || 'N/A',
          hsn_code: item.hsn_code || item.hsn || item.hsn_sac || item.commodity_code || 'N/A',
          status: item.pushed_to_zoho ? 'Completed' : 'Pending'
        };
      });

      console.log("Processed Items data:", transformedItems);
      setItemsData(transformedItems);
      setIsLoading(false);

      // Clear any previous error alerts on successful fetch
      hideSnackbarAlert();

    } catch (error) {
      console.error('Error fetching Items dashboard data:', error);
      
      // Show error alert with detailed message
      showSnackbarAlert('error', `Failed to load Items dashboard data: ${error.message}`);

      // Set loading to false even on error but keep previous data
      setDashboardData(prev => ({ ...prev, loading: false }));
      setIsLoading(false);
    }
  };

  // Fetch all data on component mount and set up interval
  useEffect(() => {
    console.log("Items Component mounted, starting data fetch...");
    
    // Initial fetch when component mounts
    fetchAllDashboardData();
    
    // Set up interval to fetch data every 10 seconds
    const intervalId = setInterval(() => {
      console.log("Interval triggered, fetching Items data...");
      fetchAllDashboardData();
    }, 10000); // 10 seconds = 10000 milliseconds

    // Cleanup interval on component unmount
    return () => {
      console.log("Items Component unmounting, clearing interval...");
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
              <h1>Items</h1>
              <p>Monitor and manage your items migration process from a single dashboard</p>
            </div>
            <div className="header-right">
              <button onClick={refreshData} className="refresh-btn" title="Refresh Data">
                🔄
              </button>
              <Bell className="notification-icon" />
              <div className="user-profile">
                <User className="user-icon" />
                <span>John Andrew</span>
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
            Items Records Count: {itemsData.length}<br/>
            Auth Token: {getAuthToken() ? 'Present' : 'Missing'}
          </div>

          {/* Stats Cards */}
          <div className="stats-grid">
            <div className="stat-card blue">
              <div className="stat-icon">
                <Package size={24} />
              </div>
              <div className="stat-content">
                <h3>Items Fetched from Tally</h3>
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
                <h3>Items Migrated to Zoho Books</h3>
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
            {/* Items Table */}
            <div className="content-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>Items</h3>
                {isLoading && <span className="loading-spinner">⟳ Loading...</span>}
              </div>
              
              <div className="table-container">
                <table className="activities-table">
                  <thead>
                    <tr>
                      <th>S.No</th>
                      <th>Name</th>
                      <th>Rate</th>
                      <th>Description</th>
                      <th>SKU</th>
                      <th>Product Type</th>
                      <th>Account</th>
                      <th>GST Rate</th>
                      <th>HSN Code</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {itemsData.length > 0 ? (
                      itemsData.map((item) => (
                        <tr key={item.sNo}>
                          <td>{item.sNo}</td>
                          <td>{item.name}</td>
                          <td>{item.rate}</td>
                          <td>{item.description}</td>
                          <td>{item.sku}</td>
                          <td>{item.product_type}</td>
                          <td>{item.account}</td>
                          <td>{item.gst_rate}</td>
                          <td>{item.hsn_code}</td>
                          <td>
                            <span className={`status ${item.status.toLowerCase().replace(' ', '-')}`}>
                              {item.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="10" style={{ textAlign: 'center', padding: '40px' }}>
                          {isLoading ? (
                            <div>Loading items...</div>
                          ) : (
                            <div className="no-data">
                              <div className="no-data-icon">📦</div>
                              <p>No Items Data Found: Manage Migration from One Dashboard</p>
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

export default ItemsDashboard;
