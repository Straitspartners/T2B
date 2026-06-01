import React, { useState, useEffect } from "react";
import { Bell, User } from "lucide-react";
import "./Dashboard.css";
import "./QuickMigration.css";
import Sidebar from "../../../components/Sidebar";

function QuickMigration() {
  const userName =
    JSON.parse(localStorage.getItem("userData") || "{}")?.name ||
    localStorage.getItem("userName") ||
    "User";

  const [isSync, setIsSync] = useState(false);
  const [progress, setProgress] = useState(0);
  const [syncedRecords, setSyncedRecords] = useState({
    masters: 0,
    transactions: 0,
    total: 0,
  });
  const [syncStatus, setSyncStatus] = useState("Ready to sync");

  const [tallyData, setTallyData] = useState({
    masters: { migrated: 0, pending: 0, total: 0, loading: true },
    transactions: { migrated: 0, pending: 0, total: 0, loading: true },
  });

  const [snackbarAlert, setSnackbarAlert] = useState({
    show: false,
    type: "",
    message: "",
  });

  const getTotalRecords = () =>
    tallyData.masters.total + tallyData.transactions.total;

  const getTotalSyncedRecords = () =>
    syncedRecords.masters + syncedRecords.transactions;

  const calculateProgress = () => {
    const totalRecords = getTotalRecords();
    const totalSynced = getTotalSyncedRecords();
    if (totalRecords === 0) return 0;
    return Math.round((totalSynced / totalRecords) * 100);
  };

  const showSnackbarAlert = (type, message) => {
    setSnackbarAlert({ show: true, type, message });
  };

  const hideSnackbarAlert = () => {
    setSnackbarAlert({ show: false, type: "", message: "" });
  };

  // -------------------- FETCH TALLY DATA --------------------

  const fetchTallyData = async () => {
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        throw new Error("Authentication token not found. Please login again.");
      }

      const response = await fetch("http://127.0.0.1:8000/api/total-records/", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch total records: ${response.status} - ${errorText}`);
      }

      const data = await response.json();

      setTallyData({
        masters: {
          migrated: data.migrated || 0,
          pending: data.pending || 0,
          total: data.total || data.vendors || data.accounts || data.ledgers || 0,
          loading: false,
        },
        transactions: {
          migrated: data.transactions_migrated || 0,
          pending: data.transactions_pending || 0,
          total: data.total_trans || 0,
          loading: false,
        },
      });

      hideSnackbarAlert();
    } catch (error) {
      console.error("Error fetching tally data:", error);
      showSnackbarAlert("error", `Failed to load Tally data: ${error.message}`);
      setTallyData((prev) => ({
        masters: { ...prev.masters, loading: false },
        transactions: { ...prev.transactions, loading: false },
      }));
    }
  };

  useEffect(() => {
    fetchTallyData();
    const intervalId = setInterval(fetchTallyData, 30000);
    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -------------------- SYNC NOW --------------------

  const handleSyncNow = async () => {
    try {
      setIsSync(true);
      setProgress(0);
      setSyncedRecords({ masters: 0, transactions: 0, total: 0 });
      setSyncStatus("Preparing sync from Tally to Zoho Books...");
      hideSnackbarAlert();

      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        throw new Error("Authentication token not found. Please login again.");
      }

      const syncResponse = await fetch("http://127.0.0.1:8000/api/push-to-zoho/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          masters: tallyData.masters,
          transactions: tallyData.transactions,
          syncType: "full",
        }),
      });

      if (!syncResponse.ok) {
        throw new Error(`Failed: ${syncResponse.status} ${syncResponse.statusText}`);
      }

      const syncResult = await syncResponse.json();

      // Simulate progress steps
      setSyncStatus("Syncing masters...");
      setProgress(40);
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setSyncStatus("Syncing transactions...");
      setProgress(80);
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setProgress(100);
      setSyncedRecords({
        masters: tallyData.masters.total,
        transactions: tallyData.transactions.total,
        total: tallyData.masters.total + tallyData.transactions.total,
      });

      setSyncStatus(syncResult.message || "Sync completed successfully!");
      showSnackbarAlert("success", syncResult.message || "Sync completed successfully!");
      fetchTallyData();
    } catch (error) {
      console.error("Error during sync:", error);
      showSnackbarAlert("error", `Failed to sync:\n${error.message}`);
      setSyncStatus("Sync failed. Please try again.");
      setProgress(0);
      setSyncedRecords({ masters: 0, transactions: 0, total: 0 });
    } finally {
      setIsSync(false);
    }
  };

  // -------------------- RENDER --------------------

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <Sidebar />

        <div className="main-content">
          {/* Header */}
          <div className="header">
            <div className="header-left">
              <h1>Quick Migration</h1>
              <p>
                Meet the Unified Migration Hub: Your key resource for smooth
                master and transaction migrations.
              </p>
            </div>
            <div className="header-right">
              <Bell className="notification-icon" />
              <div className="user-profile">
                <User className="user-icon" />
                <span>{userName}</span>
              </div>
            </div>
          </div>

          {/* Snackbar Alert */}
          {snackbarAlert.show && (
            <div className={`snackbar-alert ${snackbarAlert.type}`}>
              <div className="snackbar-content">
                <div className="snackbar-icon">
                  {snackbarAlert.type === "error"
                    ? "❌"
                    : snackbarAlert.type === "success"
                    ? "✅"
                    : snackbarAlert.type === "warning"
                    ? "⚠️"
                    : "ℹ️"}
                </div>
                <div className="snackbar-message">
                  {snackbarAlert.message.split("\n").map((line, index) => (
                    <div key={index} className="snackbar-line">
                      {line}
                    </div>
                  ))}
                </div>
                <button className="snackbar-close" onClick={hideSnackbarAlert}>
                  ×
                </button>
              </div>
            </div>
          )}

          {/* Stats Cards */}
          <div className="stats-grid">
            {/* Masters Card */}
            <div className="stat-card yellow1">
              <div className="stat-content">
                <h3 style={{ fontWeight: "bold", fontSize: "18px" }}>
                  Masters
                  {tallyData.masters.loading && (
                    <span className="loading-spinner">⟳</span>
                  )}
                </h3>
                <div style={{ marginTop: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Migrated Data in the Masters Field.</span>
                    <span style={{ fontWeight: "600" }}>
                      {tallyData.masters.loading ? "Loading..." : tallyData.masters.migrated.toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Pending records in the Masters Field.</span>
                    <span style={{ fontWeight: "600" }}>
                      {tallyData.masters.loading ? "Loading..." : tallyData.masters.pending.toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Total Records in the Masters Field.</span>
                    <span style={{ fontWeight: "600", background: "#ffeb3b", padding: "2px 4px" }}>
                      {tallyData.masters.loading ? "Loading..." : tallyData.masters.total.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Transactions Card */}
            <div className="stat-card yellow1">
              <div className="stat-content">
                <h3 style={{ fontWeight: "bold", fontSize: "18px" }}>
                  Transactions
                  {tallyData.transactions.loading && (
                    <span className="loading-spinner">⟳</span>
                  )}
                </h3>
                <div style={{ marginTop: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Migrated Data in the Transaction field.</span>
                    <span style={{ fontWeight: "600" }}>
                      {tallyData.transactions.loading ? "Loading..." : tallyData.transactions.migrated.toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Pending records in Transaction field</span>
                    <span style={{ fontWeight: "600" }}>
                      {tallyData.transactions.loading ? "Loading..." : tallyData.transactions.pending.toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Total Records</span>
                    <span style={{ fontWeight: "600", background: "#ffeb3b", padding: "2px 4px" }}>
                      {tallyData.transactions.loading ? "Loading..." : tallyData.transactions.total.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Sync Card */}
            <div className="stat-card yellow1">
              <div className="stat-content">
                <h3 style={{ fontWeight: "bold", fontSize: "18px" }}>
                  Sync Your Data in One Place
                </h3>
                <p>
                  The sync process transfers Tally data to Zoho Books and keeps
                  master data updated across both systems.
                </p>
              </div>
              <div className="sync-button-container">
                <button
                  className={`sync-button ${isSync ? "syncing" : ""}`}
                  onClick={handleSyncNow}
                  disabled={
                    isSync ||
                    tallyData.masters.loading ||
                    tallyData.transactions.loading
                  }
                >
                  {isSync ? "Syncing..." : "Sync Now"}
                </button>
              </div>
            </div>
          </div>

          {/* Progress Section */}
          <div className="current-status-section">
            <div className="status-card-progress">
              <h2 className="status-title">Current Status</h2>
              <div className="status-info-progress">
                <p className="status-description">
                  Combined Records -{" "}
                  {getTotalSyncedRecords().toLocaleString()} of{" "}
                  {getTotalRecords().toLocaleString()} synced
                  <br />
                  <small style={{ color: "#666", fontSize: "12px" }}>
                    Masters: {syncedRecords.masters.toLocaleString()}/
                    {tallyData.masters.total.toLocaleString()} | Transactions:{" "}
                    {syncedRecords.transactions.toLocaleString()}/
                    {tallyData.transactions.total.toLocaleString()}
                  </small>
                </p>

                <div className="progress-container">
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${progress}%`, transition: "width 0.5s ease" }}
                    ></div>
                  </div>
                </div>

                <div className="progress-percentage-container">
                  <span className="progress-percentage-text">
                    {progress}% completed
                  </span>
                </div>

                <div className="sync-status-text">{syncStatus}</div>
              </div>
            </div>
          </div>

          <div className="status-illustration-container">
            <div className="person-laptop-illustration">
              <div className="laptop-screen">
                <div className="screen-content"></div>
              </div>
              <div className="person-figure">
                <div className="person-head"></div>
                <div className="person-body"></div>
                <div className="person-arm"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QuickMigration;