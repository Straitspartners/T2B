import React from 'react';
import DashboardPage from './DashboardPage';
import { useDashboard } from './useDashboard';

const transform = (list) =>
  list.map((a, i) => ({
    sNo: i + 1,
    account_name: a.account_name || a.name || 'N/A',
    account_code: a.account_code || a.ledger_code || a.code || 'N/A',
    account_type: a.account_type || a.parent || 'N/A',
    status: a.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

export default function ChartofAccounts() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('coadashboard', transform, 'all_ledgers');

  return (
    <DashboardPage title="Chart of Accounts" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Chart of Accounts</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container">
            <table className="activities-table">
              <thead>
                <tr>
                  {['S.No','Account Name','Account Code','Account Type','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td><td>{r.account_name}</td>
                    <td>{r.account_code}</td><td>{r.account_type}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="5" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">📊</div><p>No accounts found</p></div>}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardPage>
  );
}