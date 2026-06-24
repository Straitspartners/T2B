import React from 'react';
import DashboardPage from './DashboardPage';
import { useDashboard } from './useDashboard';

const transform = (list) =>
  list.map((c, i) => ({
    sNo: i + 1,
    name: c.name || 'N/A',
    parent: c.parent || 'N/A',
    email: c.email || 'N/A',
    website: c.website || 'N/A',
    mobile: c.ledger_mobile || 'N/A',
    state: c.state_name || 'N/A',
    pincode: c.pincode || 'N/A',
    country: c.country_name || 'N/A',
    status: c.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

export default function Customers() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('dashboard/customers', transform, 'all_ledgers');

  return (
    <DashboardPage title="Customers" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Customers</h3>
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
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">📊</div><p>No customers found</p></div>}
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