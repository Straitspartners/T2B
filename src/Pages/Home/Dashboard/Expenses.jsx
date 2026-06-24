import React from 'react';
import { Wallet } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard, formatDate, formatAmount } from './useDashboard';

const transform = (list) =>
  list.map((exp, i) => ({
    sNo: i + 1,
    expense_number: exp.expense_number || exp.voucher_number || exp.number || 'N/A',
    expense_date: exp.expense_date || exp.date || exp.voucher_date || 'N/A',
    paid_through: exp.paid_through || exp.account || exp.payment_account || 'N/A',
    vendor: exp.vendor || exp.vendor_name || exp.party_name || 'N/A',
    amount: exp.amount || exp.total_amount || exp.expense_amount || 'N/A',
    category: exp.category || exp.expense_account || exp.account_name || 'N/A',
    description: exp.description || exp.narration || exp.notes || 'N/A',
    zoho_expense_id: exp.zoho_expense_id || exp.expense_id || 'N/A',
    status: exp.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Expenses Fetched from Tally',    icon: <Wallet size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Expenses Migrated to Zoho Books', icon: <Wallet size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',               icon: <Wallet size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function Expenses() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('dashboard/expenses', transform, 'all_expenses');

  return (
    <DashboardPage title="Expenses" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Expenses</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="activities-table" style={{ minWidth: 1100 }}>
              <thead>
                <tr>
                  {['S.No','Expense No.','Date','Paid Through','Vendor','Amount','Category','Description','Zoho Expense ID','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td>
                    <td>{r.expense_number}</td>
                    <td>{formatDate(r.expense_date)}</td>
                    <td>{r.paid_through}</td>
                    <td>{r.vendor}</td>
                    <td>{formatAmount(r.amount)}</td>
                    <td>{r.category}</td>
                    <td>{r.description}</td>
                    <td>{r.zoho_expense_id}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="10" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">💰</div><p>No expenses found</p></div>}
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