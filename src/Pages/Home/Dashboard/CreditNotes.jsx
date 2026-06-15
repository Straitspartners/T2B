import React from 'react';
import { FileMinus } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard, formatDate, formatAmount } from './useDashboard';

const transform = (list) =>
  list.map((cn, i) => ({
    sNo: i + 1,
    credit_note_number: cn.credit_note_number || cn.voucher_number || cn.number || 'N/A',
    credit_note_date: cn.credit_note_date || cn.date || cn.voucher_date || 'N/A',
    customer: cn.customer || cn.customer_name || cn.party_name || 'N/A',
    amount: cn.amount || cn.total_amount || 'N/A',
    reason: cn.reason || cn.narration || cn.description || 'N/A',
    zoho_credit_note_id: cn.zoho_credit_note_id || cn.credit_note_id || 'N/A',
    status: cn.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Credit Notes Fetched from Tally',    icon: <FileMinus size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Credit Notes Migrated to Zoho Books', icon: <FileMinus size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',                   icon: <FileMinus size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function CreditNotes() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('creditnotedashboard', transform, 'all_credit_notes');

  return (
    <DashboardPage title="Credit Notes" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Credit Notes</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="activities-table" style={{ minWidth: 900 }}>
              <thead>
                <tr>
                  {['S.No','Credit Note No.','Date','Customer','Amount','Reason','Zoho Credit Note ID','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td>
                    <td>{r.credit_note_number}</td>
                    <td>{formatDate(r.credit_note_date)}</td>
                    <td>{r.customer}</td>
                    <td>{formatAmount(r.amount)}</td>
                    <td>{r.reason}</td>
                    <td>{r.zoho_credit_note_id}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="8" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">📋</div><p>No credit notes found</p></div>}
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
