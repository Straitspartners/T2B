import React from 'react';
import DashboardPage from './DashboardPage';
import { useDashboard } from './useDashboard';

const transform = (list) =>
  list.map((v, i) => ({
    sNo: i + 1,
    name: v.name || 'N/A',
    parent: v.parent || 'N/A',
    email: v.email || 'N/A',
    website: v.website || 'N/A',
    mobile: v.ledger_mobile || 'N/A',
    state: v.state_name || 'N/A',
    pincode: v.pincode || 'N/A',
    country: v.country_name || 'N/A',
    status: v.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

export default function Vendors() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('vendordashboard', transform, 'all_ledgers');

  return (
    <DashboardPage title="Vendors" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Vendors</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container">
            <table className="activities-table">
              <thead>
                <tr>
                  {['S.No','Name','Parent','Email','Website','Mobile','State','Pincode','Country','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td><td>{r.name}</td><td>{r.parent}</td>
                    <td>{r.email}</td><td>{r.website}</td><td>{r.mobile}</td>
                    <td>{r.state}</td><td>{r.pincode}</td><td>{r.country}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="10" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">📊</div><p>No vendors found</p></div>}
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