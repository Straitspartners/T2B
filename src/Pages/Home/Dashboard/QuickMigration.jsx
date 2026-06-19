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
  const [syncStatus, setSyncStatus] = useState("Ready to sync");
  const [syncDetails, setSyncDetails] = useState(null); // per-type results table
  const [lastSyncStats, setLastSyncStats] = useState(null); // { success, failed, skipped, total }

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
    tallyData.masters.migrated + tallyData.transactions.migrated;

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
  // Single source of truth for BOTH the top cards (Migrated/Pending/Total)
  // AND the progress bar. Both read from this same tallyData state now,
  // so they can never disagree (this fixed the "Migrated: 0" vs "100%
  // completed" mismatch you saw).

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
      return data;
    } catch (error) {
      console.error("Error fetching tally data:", error);
      showSnackbarAlert("error", `Failed to load Tally data: ${error.message}`);
      setTallyData((prev) => ({
        masters: { ...prev.masters, loading: false },
        transactions: { ...prev.transactions, loading: false },
      }));
      return null;
    }
  };

  // Background polling — runs always, every 30s, whether or not a sync
  // is in progress. Keeps the cards fresh and drives the live progress
  // bar during a sync (no more fake/simulated progress).
  useEffect(() => {
    fetchTallyData();
    const intervalId = setInterval(fetchTallyData, 30000);
    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // NOTE: We intentionally do NOT auto-detect completion by comparing
  // synced vs total record counts. Skipped and failed records never
  // become "migrated", so that comparison can never reach 100% and would
  // leave isSync stuck forever. Completion is now detected directly from
  // the push-to-zoho response in handleSyncNow (it's a synchronous call).

  // -------------------- SYNC NOW --------------------

  const handleSyncNow = async () => {
    try {
      setIsSync(true);
      setSyncDetails(null);
      setSyncStatus("Starting sync — pushing data to Zoho Books...");
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
          types: ["customers", "vendors", "accounts", "items", "taxes", "invoices", "receipts", "bills", "payments", "credit_notes", "vendor_credits", "journals", "opening_balances", "expenses"],
        }),
      });

      const rawText = await syncResponse.text();
      let syncResult;
      try {
        syncResult = JSON.parse(rawText);
      } catch {
        throw new Error(`Server returned unexpected response: ${rawText}`);
      }

      // Debug: log the raw shape once so we can see exactly what key
      // the backend uses for per-type results.
      console.log("push-to-zoho response:", syncResult);

      // 207 = Multi-Status, used here because some types succeeded and
      // some failed. Treat it as a valid completed response, not an error.
      if (!syncResponse.ok && syncResponse.status !== 202 && syncResponse.status !== 207) {
        const djangoError = syncResult?.error || syncResult?.message || `HTTP ${syncResponse.status}`;
        throw new Error(djangoError);
      }

      // The push endpoint is SYNCHRONOUS — by the time fetch() resolves,
      // the backend has already finished pushing everything. The Django
      // view (migration/views.py push_to_zoho) returns per-type results
      // under the key "details" — e.g.
      //   { message, total_success, total_failed, total_skipped, details: {...} }
      const results = syncResult?.details || null;

      if (results && typeof results === "object") {
        setSyncDetails(results);
      }

      await fetchTallyData();

      const totalSuccess = syncResult?.total_success ?? 0;
      const totalFailed = syncResult?.total_failed ?? 0;
      const totalSkipped = syncResult?.total_skipped ?? 0;
      const totalProcessed = totalSuccess + totalFailed + totalSkipped;

      setLastSyncStats({
        success: totalSuccess,
        failed: totalFailed,
        skipped: totalSkipped,
        total: totalProcessed,
        // "success rate" of this run — pushed vs everything attempted,
        // excluding already-skipped (already-synced) records from the
        // denominator so it reflects this run's actual work, not the
        // lifetime total.
        percent:
          totalSuccess + totalFailed > 0
            ? Math.round((totalSuccess / (totalSuccess + totalFailed)) * 100)
            : 100,
      });

      setSyncStatus(
        `Sync completed — ${totalSuccess.toLocaleString()} pushed, ${totalSkipped.toLocaleString()} skipped, ${totalFailed.toLocaleString()} failed.`
      );
      setIsSync(false);
      showSnackbarAlert(
        results ? "success" : "warning",
        results
          ? "✅ Sync completed!"
          : "⚠️ Sync finished but couldn't read per-type results — check browser console."
      );
    } catch (error) {
      console.error("Error during sync:", error);
      showSnackbarAlert("error", `Failed to sync: ${error.message}`);
      setSyncStatus(`Sync failed: ${error.message}`);
      setIsSync(false);
    }
  };

  const progress = calculateProgress();

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

                {isSync ? (
                  // ───────── ACTIVE SYNC: show live progress bar ─────────
                  <>
                    <p className="status-description">
                      Combined Records —{" "}
                      {getTotalSyncedRecords().toLocaleString()} of{" "}
                      {getTotalRecords().toLocaleString()} synced
                      <br />
                      <small style={{ color: "#666", fontSize: "12px" }}>
                        Masters: {tallyData.masters.migrated.toLocaleString()}/
                        {tallyData.masters.total.toLocaleString()} | Transactions:{" "}
                        {tallyData.transactions.migrated.toLocaleString()}/
                        {tallyData.transactions.total.toLocaleString()}
                      </small>
                    </p>

                    <div className="progress-container">
                      <div className="progress-bar-bg">
                        <div
                          className="progress-bar-fill syncing"
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
                  </>
                ) : syncDetails ? (
                  // ───────── SYNC FINISHED: show final % + results table, no live bar ─────────
                  <>
                    <p className="status-description">
                      Last sync finished at{" "}
                      <strong>{lastSyncStats?.percent ?? progress}%</strong> success rate —{" "}
                      {(lastSyncStats?.success ?? 0).toLocaleString()} pushed,{" "}
                      {(lastSyncStats?.skipped ?? 0).toLocaleString()} skipped,{" "}
                      {(lastSyncStats?.failed ?? 0).toLocaleString()} failed
                    </p>
                    <div className="sync-status-text">{syncStatus}</div>
                  </>
                ) : (
                  // ───────── NEVER SYNCED YET / IDLE: calm summary, no bar ─────────
                  <>
                    <p className="status-description">
                      {getTotalRecords().toLocaleString()} total records found —{" "}
                      {getTotalSyncedRecords().toLocaleString()} already in Zoho Books
                    </p>
                    <div className="sync-status-text">{syncStatus}</div>
                  </>
                )}

                {/* Per-type breakdown table — shown whenever we have
                    results, whether mid-sync (polled) or after completion */}
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
                            <td style={{ padding: "6px 10px", textTransform: "capitalize" }}>{type.replace(/_/g, " ")}</td>
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