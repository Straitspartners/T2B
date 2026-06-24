import React from 'react';
import { FileText } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard, formatDate, formatAmount } from './useDashboard';

const transform = (list) =>
  list.map((inv, i) => ({
    sNo: i + 1,
    invoice_number: inv.invoice_number || inv.voucher_number || inv.number || 'N/A',
    invoice_date: inv.invoice_date || inv.date || inv.voucher_date || 'N/A',
    due_date: inv.due_date || inv.payment_due_date || 'N/A',
    customer: inv.customer || inv.customer_name || inv.party_name || 'N/A',
    amount: inv.amount || inv.total_amount || inv.invoice_amount || 'N/A',
    balance_due: inv.balance_due || inv.outstanding_amount || 'N/A',
    zoho_invoice_id: inv.zoho_invoice_id || inv.invoice_id || 'N/A',
    status: inv.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Invoices Fetched from Tally',    icon: <FileText size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Invoices Migrated to Zoho Books', icon: <FileText size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',               icon: <FileText size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function Invoice() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('dashboard/invoices', transform, 'all_invoices');

  return (
    <DashboardPage title="Invoices" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Invoices</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="activities-table" style={{ minWidth: 1100 }}>
              <thead>
                <tr>
                  {['S.No','Invoice No.','Invoice Date','Due Date','Customer','Amount','Balance Due','Zoho Invoice ID','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td>
                    <td>{r.invoice_number}</td>
                    <td>{formatDate(r.invoice_date)}</td>
                    <td>{formatDate(r.due_date)}</td>
                    <td>{r.customer}</td>
                    <td>{formatAmount(r.amount)}</td>
                    <td>{formatAmount(r.balance_due)}</td>
                    <td>{r.zoho_invoice_id}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="9" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">📄</div><p>No invoices found</p></div>}
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