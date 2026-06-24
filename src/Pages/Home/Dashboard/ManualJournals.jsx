import React from 'react';
import { BookOpen } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard, formatDate, formatAmount } from './useDashboard';

const transform = (list) =>
  list.map((j, i) => ({
    sNo: i + 1,
    journal_date: j.journal_date || j.date || j.voucher_date || 'N/A',
    journal_number: j.journal_number || j.voucher_number || j.number || 'N/A',
    reference_number: j.reference_number || j.ref_number || j.reference || 'N/A',
    notes: j.notes || j.narration || j.description || 'N/A',
    debit_total: j.debit_total || j.total_debit || 'N/A',
    credit_total: j.credit_total || j.total_credit || 'N/A',
    zoho_journal_id: j.zoho_journal_id || j.journal_id || 'N/A',
    status: j.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Journals Fetched from Tally',    icon: <BookOpen size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Journals Migrated to Zoho Books', icon: <BookOpen size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',               icon: <BookOpen size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function ManualJournals() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('dashboard/journals', transform, 'all_journals');

  return (
    <DashboardPage title="Manual Journals" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Manual Journals</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="activities-table" style={{ minWidth: 1000 }}>
              <thead>
                <tr>
                  {['S.No','Journal Date','Journal No.','Reference No.','Notes','Debit Total','Credit Total','Zoho Journal ID','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td>
                    <td>{formatDate(r.journal_date)}</td>
                    <td>{r.journal_number}</td>
                    <td>{r.reference_number}</td>
                    <td>{r.notes}</td>
                    <td>{formatAmount(r.debit_total)}</td>
                    <td>{formatAmount(r.credit_total)}</td>
                    <td>{r.zoho_journal_id}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="9" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">📒</div><p>No journal entries found</p></div>}
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