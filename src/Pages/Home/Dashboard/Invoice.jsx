import React, { useState, useEffect } from 'react';
import { Bell, User, BarChart3, CreditCard, Receipt } from 'lucide-react';
import './Dashboard.css';
import Sidebar from '../../../components/Sidebar';

function ReceiptDashboard() {
  const [dashboardData, setDashboardData] = useState({
    dataFetchedFromTally: 0,
    dataMigratedToZoho: 0,
    pendingMigration: 0,
    loading: true
  });
  
  const [receiptsData, setReceiptsData] = useState([]);
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

  // Format date helper function
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit'
      });
    } catch (error) {
      return dateString;
    }
  };

  // Format amount helper function
  const formatAmount = (amount) => {
    if (!amount || amount === 'N/A') return 'N/A';
    try {
      return parseFloat(amount).toLocaleString('en-US', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
      });
    } catch (error) {
      return amount;
    }
  };

  // Single API call to fetch all dashboard data
  const fetchAllDashboardData = async () => {
    try {
      console.log("Starting fetchAllDashboardData for Receipts...");
      
      const authToken = getAuthToken();
      console.log("Auth token:", authToken ? "Present" : "Missing");
      
      if (!authToken) {
        throw new Error('Authentication token not found. Please login again.');
      }

      // Receipt API endpoint
      const endpoint = `https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/receiptdashboard/`;
      
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`
        }
      });

      console.log("Receipt dashboard response status:", response.status);
      console.log("Receipt dashboard response ok:", response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Receipt dashboard response error:", errorText);
        throw new Error(`Failed to fetch Receipt dashboard data: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log("Receipt dashboard raw API response:", data);
      console.log("API Response Keys:", Object.keys(data));
      
      // Log the first few receipts to see structure
      const receiptsApiData = data.all_receipts || data.receipts || data.all_ledgers || [];
      console.log("Receipts array length:", receiptsApiData.length);
      if (receiptsApiData.length > 0) {
        console.log("First receipt structure:", receiptsApiData[0]);
        console.log("First receipt keys:", Object.keys(receiptsApiData[0]));
      }
      
      // Update dashboard statistics from summary data
      setDashboardData({
        dataFetchedFromTally: data.summary?.fetched_from_tally || 0,
        dataMigratedToZoho: data.summary?.pushed_to_zoho || 0,
        pendingMigration: (data.summary?.fetched_from_tally || 0) - (data.summary?.pushed_to_zoho || 0),
        loading: false
      });

      // Transform receipts data with extensive field mapping
      const transformedReceipts = receiptsApiData.map((receipt, index) => {
        console.log(`Receipt ${index + 1} raw data:`, receipt);
        return {
          sNo: index + 1,
          user: receipt.user || receipt.user_name || receipt.created_by || 'N/A',
          receipt_number: receipt.receipt_number || receipt.receipt_no || receipt.number || 'N/A',
          receipt_date: receipt.receipt_date || receipt.date || receipt.transaction_date || 'N/A',
          amount: receipt.amount || receipt.total_amount || receipt.receipt_amount || 'N/A',
          payment_mode: receipt.payment_mode || receipt.payment_method || receipt.mode || 'N/A',
          customer: receipt.customer || receipt.customer_name || receipt.party || receipt.party_name || 'N/A',
          customer_zoho_id: receipt.customer_zoho_id || receipt.zoho_customer_id || 'N/A',
          agst_invoice: receipt.agst_invoice || receipt.against_invoice || receipt.invoice_ref || 'N/A',
          invoice_zoho_id: receipt.invoice_zoho_id || receipt.zoho_invoice_id || 'N/A',
          invoice_total_amount: receipt.invoice_total_amount || receipt.invoice_amount || 'N/A',
          zoho_receipt_id: receipt.zoho_receipt_id || receipt.receipt_id || 'N/A',
          created_at: receipt.created_at || receipt.created_date || 'N/A',
          fetched_from_tally: receipt.fetched_from_tally ? 'Yes' : 'No',
          pushed_to_zoho: receipt.pushed_to_zoho ? 'Yes' : 'No',
          status: receipt.pushed_to_zoho ? 'Completed' : 'Pending'
        };
      });

      console.log("Processed Receipts data:", transformedReceipts);
      setReceiptsData(transformedReceipts);
      setIsLoading(false);

      // Clear any previous error alerts on successful fetch
      hideSnackbarAlert();

    } catch (error) {
      console.error('Error fetching Receipt dashboard data:', error);
      
      // Show error alert with detailed message
      showSnackbarAlert('error', `Failed to load Receipt dashboard data: ${error.message}`);

      // Set loading to false even on error but keep previous data
      setDashboardData(prev => ({ ...prev, loading: false }));
      setIsLoading(false);
    }
  };

  // Fetch all data on component mount and set up interval
  useEffect(() => {
    console.log("Receipt Component mounted, starting data fetch...");
    
    // Initial fetch when component mounts
    fetchAllDashboardData();
    
    // Set up interval to fetch data every 10 seconds
    const intervalId = setInterval(() => {
      console.log("Interval triggered, fetching Receipt data...");
      fetchAllDashboardData();
    }, 10000); // 10 seconds = 10000 milliseconds

    // Cleanup interval on component unmount
    return () => {
      console.log("Receipt Component unmounting, clearing interval...");
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
              <h1>Receipts</h1>
              <p>Monitor and manage your receipts migration process from a single dashboard</p>
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
            Receipt Records Count: {receiptsData.length}<br/>
            Auth Token: {getAuthToken() ? 'Present' : 'Missing'}
          </div>

          {/* Stats Cards */}
          <div className="stats-grid">
            <div className="stat-card blue">
              <div className="stat-icon">
                <Receipt size={24} />
              </div>
              <div className="stat-content">
                <h3>Receipts Fetched from Tally</h3>
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
                <h3>Receipts Migrated to Zoho Books</h3>
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
            {/* Receipts Table */}
            <div className="content-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>Receipts</h3>
                {isLoading && <span className="loading-spinner">⟳ Loading...</span>}
              </div>
              
              <div className="table-container" style={{ overflowX: 'auto' }}>
                <table className="activities-table" style={{ minWidth: '1800px' }}>
                  <thead>
                    <tr>
                      <th>S.No</th>
                      <th>User</th>
                      <th>Receipt Number</th>
                      <th>Receipt Date</th>
                      <th>Amount</th>
                      <th>Payment Mode</th>
                      <th>Customer</th>
                      <th>Customer Zoho ID</th>
                      <th>Against Invoice</th>
                      <th>Invoice Zoho ID</th>
                      <th>Invoice Total Amount</th>
                      <th>Zoho Receipt ID</th>
                      <th>Created At</th>
                      <th>Fetched from Tally</th>
                      <th>Pushed to Zoho</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {receiptsData.length > 0 ? (
                      receiptsData.map((receipt) => (
                        <tr key={receipt.sNo}>
                          <td>{receipt.sNo}</td>
                          <td>{receipt.user}</td>
                          <td>{receipt.receipt_number}</td>
                          <td>{formatDate(receipt.receipt_date)}</td>
                          <td>{formatAmount(receipt.amount)}</td>
                          <td>{receipt.payment_mode}</td>
                          <td>{receipt.customer}</td>
                          <td>{receipt.customer_zoho_id}</td>
                          <td>{receipt.agst_invoice}</td>
                          <td>{receipt.invoice_zoho_id}</td>
                          <td>{formatAmount(receipt.invoice_total_amount)}</td>
                          <td>{receipt.zoho_receipt_id}</td>
                          <td>{formatDate(receipt.created_at)}</td>
                          <td>
                            <span className={`status ${receipt.fetched_from_tally === 'Yes' ? 'completed' : 'pending'}`}>
                              {receipt.fetched_from_tally}
                            </span>
                          </td>
                          <td>
                            <span className={`status ${receipt.pushed_to_zoho === 'Yes' ? 'completed' : 'pending'}`}>
                              {receipt.pushed_to_zoho}
                            </span>
                          </td>
                          <td>
                            <span className={`status ${receipt.status.toLowerCase().replace(' ', '-')}`}>
                              {receipt.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="16" style={{ textAlign: 'center', padding: '40px' }}>
                          {isLoading ? (
                            <div>Loading receipts...</div>
                          ) : (
                            <div className="no-data">
                              <div className="no-data-icon">🧾</div>
                              <p>No Receipt Data Found: Manage Migration from One Dashboard</p>
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

export default ReceiptDashboard;
