import React from 'react';
import { FileMinus } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard, formatDate, formatAmount } from './useDashboard';

const transform = (list) =>
  list.map((vc, i) => ({
    sNo: i + 1,
    vendor_credit_number: vc.vendor_credit_number || vc.voucher_number || vc.number || 'N/A',
    vendor_credit_date: vc.vendor_credit_date || vc.date || vc.voucher_date || 'N/A',
    vendor: vc.vendor || vc.vendor_name || vc.party_name || 'N/A',
    amount: vc.amount || vc.total_amount || 'N/A',
    reason: vc.reason || vc.narration || vc.description || 'N/A',
    zoho_vendor_credit_id: vc.zoho_vendor_credit_id || vc.vendor_credit_id || 'N/A',
    status: vc.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Vendor Credits Fetched from Tally',    icon: <FileMinus size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Vendor Credits Migrated to Zoho Books', icon: <FileMinus size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',                     icon: <FileMinus size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function VendorCredit() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('dashboard/vendor-credits', transform, 'all_vendor_credits');

  return (
    <DashboardPage title="Vendor Credit" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Vendor Credits</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="activities-table" style={{ minWidth: 900 }}>
              <thead>
                <tr>
                  {['S.No','Vendor Credit No.','Date','Vendor','Amount','Reason','Zoho Vendor Credit ID','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td>
                    <td>{r.vendor_credit_number}</td>
                    <td>{formatDate(r.vendor_credit_date)}</td>
                    <td>{r.vendor}</td>
                    <td>{formatAmount(r.amount)}</td>
                    <td>{r.reason}</td>
                    <td>{r.zoho_vendor_credit_id}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="8" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">📋</div><p>No vendor credits found</p></div>}
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
