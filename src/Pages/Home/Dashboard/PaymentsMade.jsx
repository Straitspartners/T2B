import React from 'react';
import { Receipt } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard, formatDate, formatAmount } from './useDashboard';

const transform = (list) =>
  list.map((r, i) => ({
    sNo: i + 1,
    receipt_number: r.receipt_number || r.receipt_no || r.number || 'N/A',
    receipt_date: r.receipt_date || r.date || r.transaction_date || 'N/A',
    amount: r.amount || r.total_amount || 'N/A',
    payment_mode: r.payment_mode || r.payment_method || r.mode || 'N/A',
    customer: r.customer || r.customer_name || r.party_name || 'N/A',
    customer_zoho_id: r.customer_zoho_id || r.zoho_customer_id || 'N/A',
    agst_invoice: r.agst_invoice || r.against_invoice || r.invoice_ref || 'N/A',
    invoice_zoho_id: r.invoice_zoho_id || r.zoho_invoice_id || 'N/A',
    invoice_total_amount: r.invoice_total_amount || r.invoice_amount || 'N/A',
    zoho_receipt_id: r.zoho_receipt_id || r.receipt_id || 'N/A',
    fetched_from_tally: r.fetched_from_tally ? 'Yes' : 'No',
    pushed_to_zoho: r.pushed_to_zoho ? 'Yes' : 'No',
    status: r.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Receipts Fetched from Tally',    icon: <Receipt size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Receipts Migrated to Zoho Books', icon: <Receipt size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',               icon: <Receipt size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function PaymentReceived() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('receiptdashboard', transform, 'all_receipts');

  return (
    <DashboardPage title="Payment Received" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Payment Received</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="activities-table" style={{ minWidth: 1600 }}>
              <thead>
                <tr>
                  {['S.No','Receipt No.','Date','Amount','Payment Mode','Customer','Customer Zoho ID','Against Invoice','Invoice Zoho ID','Invoice Amount','Zoho Receipt ID','Fetched','Pushed','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td>
                    <td>{r.receipt_number}</td>
                    <td>{formatDate(r.receipt_date)}</td>
                    <td>{formatAmount(r.amount)}</td>
                    <td>{r.payment_mode}</td>
                    <td>{r.customer}</td>
                    <td>{r.customer_zoho_id}</td>
                    <td>{r.agst_invoice}</td>
                    <td>{r.invoice_zoho_id}</td>
                    <td>{formatAmount(r.invoice_total_amount)}</td>
                    <td>{r.zoho_receipt_id}</td>
                    <td><span className={`status ${r.fetched_from_tally === 'Yes' ? 'completed' : 'pending'}`}>{r.fetched_from_tally}</span></td>
                    <td><span className={`status ${r.pushed_to_zoho === 'Yes' ? 'completed' : 'pending'}`}>{r.pushed_to_zoho}</span></td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="14" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">🧾</div><p>No receipts found</p></div>}
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