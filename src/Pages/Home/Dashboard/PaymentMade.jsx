import React from 'react';
import { Send } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard, formatDate, formatAmount } from './useDashboard';

const transform = (list) =>
  list.map((p, i) => ({
    sNo: i + 1,
    payment_number: p.payment_number || p.voucher_number || p.number || 'N/A',
    payment_date: p.payment_date || p.date || p.voucher_date || 'N/A',
    vendor: p.vendor || p.vendor_name || p.party_name || 'N/A',
    amount: p.amount || p.total_amount || p.payment_amount || 'N/A',
    payment_mode: p.payment_mode || p.payment_method || p.mode || 'N/A',
    vendor_zoho_id: p.vendor_zoho_id || p.zoho_vendor_id || 'N/A',
    against_bill: p.against_bill || p.bill_ref || p.agst_bill || 'N/A',
    bill_zoho_id: p.bill_zoho_id || p.zoho_bill_id || 'N/A',
    zoho_payment_id: p.zoho_payment_id || p.payment_id || 'N/A',
    status: p.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Payments Fetched from Tally',    icon: <Send size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Payments Migrated to Zoho Books', icon: <Send size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',               icon: <Send size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function PaymentMade() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('paymentmadedashboard', transform, 'all_payments');

  return (
    <DashboardPage title="Payment Made" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Payments Made</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="activities-table" style={{ minWidth: 1200 }}>
              <thead>
                <tr>
                  {['S.No','Payment No.','Date','Vendor','Amount','Payment Mode','Vendor Zoho ID','Against Bill','Bill Zoho ID','Zoho Payment ID','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td>
                    <td>{r.payment_number}</td>
                    <td>{formatDate(r.payment_date)}</td>
                    <td>{r.vendor}</td>
                    <td>{formatAmount(r.amount)}</td>
                    <td>{r.payment_mode}</td>
                    <td>{r.vendor_zoho_id}</td>
                    <td>{r.against_bill}</td>
                    <td>{r.bill_zoho_id}</td>
                    <td>{r.zoho_payment_id}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="11" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">💸</div><p>No payments made found</p></div>}
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
