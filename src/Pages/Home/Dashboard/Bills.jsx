import React from 'react';
import { FileText } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard, formatDate, formatAmount } from './useDashboard';

const transform = (list) =>
  list.map((b, i) => ({
    sNo: i + 1,
    bill_number: b.bill_number || b.voucher_number || b.number || 'N/A',
    bill_date: b.bill_date || b.date || b.voucher_date || 'N/A',
    due_date: b.due_date || b.payment_due_date || 'N/A',
    vendor: b.vendor || b.vendor_name || b.party_name || 'N/A',
    amount: b.amount || b.total_amount || b.bill_amount || 'N/A',
    balance_due: b.balance_due || b.outstanding_amount || 'N/A',
    zoho_bill_id: b.zoho_bill_id || b.bill_id || 'N/A',
    status: b.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Bills Fetched from Tally',    icon: <FileText size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Bills Migrated to Zoho Books', icon: <FileText size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',            icon: <FileText size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function Bills() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('billdashboard', transform, 'all_bills');

  return (
    <DashboardPage title="Bills" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Bills</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="activities-table" style={{ minWidth: 1000 }}>
              <thead>
                <tr>
                  {['S.No','Bill No.','Bill Date','Due Date','Vendor','Amount','Balance Due','Zoho Bill ID','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td>
                    <td>{r.bill_number}</td>
                    <td>{formatDate(r.bill_date)}</td>
                    <td>{formatDate(r.due_date)}</td>
                    <td>{r.vendor}</td>
                    <td>{formatAmount(r.amount)}</td>
                    <td>{formatAmount(r.balance_due)}</td>
                    <td>{r.zoho_bill_id}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="9" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">🧾</div><p>No bills found</p></div>}
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
