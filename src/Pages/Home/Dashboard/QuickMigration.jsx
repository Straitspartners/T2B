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
  const [syncDetails, setSyncDetails] = useState(null); // ← new: per-type results

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
          total: data.total || 0,
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
    setProgress(10);
    setSyncedRecords({ masters: 0, transactions: 0, total: 0 });
    setSyncDetails(null);
    setSyncStatus("Pushing data to Zoho Books in background...");
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
        types: ["customers", "vendors", "accounts", "items", "taxes", "invoices", "receipts", "bills", "payments", "credit_notes", "vendor_credits", "journals", "expenses"],
      }),
    });

    const rawText = await syncResponse.text();
    let syncResult;
    try {
      syncResult = JSON.parse(rawText);
    } catch {
      throw new Error(`Server returned unexpected response: ${rawText}`);
    }

    if (!syncResponse.ok && syncResponse.status !== 202) {
      const djangoError = syncResult?.error || syncResult?.message || `HTTP ${syncResponse.status}`;
      throw new Error(djangoError);
    }

    // Background push started — animate progress and poll for updates
    setProgress(30);
    setSyncStatus("Sync running in background... Records will update automatically.");
    showSnackbarAlert("success", "✅ Sync started! Data is being pushed to Zoho Books. This may take 15–20 minutes. The counts below will refresh every 30 seconds.");

    // Animate progress bar slowly to show activity
    let fakeProgress = 30;
    const progressInterval = setInterval(() => {
      fakeProgress = Math.min(fakeProgress + 2, 90);
      setProgress(fakeProgress);
    }, 3000);

    // Poll every 30s to update migrated counts
    let pollCount = 0;
    const pollInterval = setInterval(async () => {
      await fetchTallyData();
      pollCount++;
      if (pollCount >= 40) { // Stop after 20 minutes
        clearInterval(pollInterval);
        clearInterval(progressInterval);
        setProgress(100);
        setSyncStatus("Sync completed! Check the counts above.");
        setIsSync(false);
      }
    }, 30000);

    // Store intervals so we don't block the UI
    setSyncStatus("Sync running in background — check server logs for live progress.");

  } catch (error) {
    console.error("Error during sync:", error);
    showSnackbarAlert("error", `Failed to sync: ${error.message}`);
    setSyncStatus(`Sync failed: ${error.message}`);
    setProgress(0);
    setIsSync(false);
  }
  // Note: setIsSync(false) NOT in finally — we want button to stay "Syncing..."
  // until poll detects completion or timeout
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
                    <span style={{ fontSize: "14px", color: "#718096" }}>Migrated</span>
                    <span style={{ fontWeight: "600" }}>
                      {tallyData.masters.loading ? "Loading..." : tallyData.masters.migrated.toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Pending</span>
                    <span style={{ fontWeight: "600" }}>
                      {tallyData.masters.loading ? "Loading..." : tallyData.masters.pending.toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Total Records</span>
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
                    <span style={{ fontSize: "14px", color: "#718096" }}>Migrated</span>
                    <span style={{ fontWeight: "600" }}>
                      {tallyData.transactions.loading ? "Loading..." : tallyData.transactions.migrated.toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ fontSize: "14px", color: "#718096" }}>Pending</span>
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
                  Pushes all Tally data — customers, vendors, accounts, items,
                  invoices, receipts, bills, payments, credit notes, vendor
                  credits and journals — into Zoho Books. Already-synced
                  records are skipped automatically.
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
                  Combined Records —{" "}
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

                {/* Per-type breakdown table shown after sync */}
                {syncDetails && (
                  <div style={{ marginTop: "16px", overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                      <thead>
                        <tr style={{ background: "#f7f7f7" }}>
                          <th style={{ padding: "6px 10px", textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>Type</th>
                          <th style={{ padding: "6px 10px", textAlign: "center", borderBottom: "1px solid #e2e8f0" }}>✅ Pushed</th>
                          <th style={{ padding: "6px 10px", textAlign: "center", borderBottom: "1px solid #e2e8f0" }}>⏭ Skipped</th>
                          <th style={{ padding: "6px 10px", textAlign: "center", borderBottom: "1px solid #e2e8f0" }}>❌ Failed</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(syncDetails).map(([type, counts]) => (
                          <tr key={type} style={{ borderBottom: "1px solid #f0f0f0" }}>
                            <td style={{ padding: "6px 10px", textTransform: "capitalize" }}>{type}</td>
                            <td style={{ padding: "6px 10px", textAlign: "center", color: "#38a169" }}>{counts.success ?? 0}</td>
                            <td style={{ padding: "6px 10px", textAlign: "center", color: "#718096" }}>{counts.skipped ?? 0}</td>
                            <td style={{ padding: "6px 10px", textAlign: "center", color: counts.failed > 0 ? "#e53e3e" : "#718096" }}>{counts.failed ?? 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
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