import React from 'react';
import { Package } from 'lucide-react';
import DashboardPage from './DashboardPage';
import { useDashboard } from './useDashboard';

const transform = (list) =>
  list.map((item, i) => ({
    sNo: i + 1,
    name: item.name || item.item_name || 'N/A',
    rate: item.rate || item.price || item.unit_price || 'N/A',
    description: item.description || item.desc || 'N/A',
    sku: item.sku || item.item_code || item.code || 'N/A',
    product_type: item.product_type || item.type || item.category || 'N/A',
    account: item.account || item.account_name || item.ledger_name || 'N/A',
    gst_rate: item.gst_rate || item.tax_rate || item.gst || 'N/A',
    hsn_code: item.hsn_code || item.hsn || item.hsn_sac || 'N/A',
    status: item.pushed_to_zoho ? 'Completed' : 'Pending',
  }));

const cardConfig = [
  { key: 'dataFetchedFromTally', label: 'Items Fetched from Tally',    icon: <Package size={24} />, color: 'blue',   change: '↗ Live Data', stroke: '#4F46E5' },
  { key: 'dataMigratedToZoho',   label: 'Items Migrated to Zoho Books', icon: <Package size={24} />, color: 'orange', change: '↗ Live Data', stroke: '#F59E0B' },
  { key: 'pendingMigration',     label: 'Pending Migration',            icon: <Package size={24} />, color: 'yellow', change: 'Live Data',   stroke: '#EAB308' },
];

export default function Items() {
  const { stats, tableData, isLoading, alert, hideAlert, refresh } =
    useDashboard('dashboard/items', transform, 'all_items');

  return (
    <DashboardPage title="Items" stats={stats} alert={alert} onHideAlert={hideAlert} onRefresh={refresh} cardConfig={cardConfig}>
      <div className="content-grid-dashboard" style={{ gridTemplateColumns: '1fr' }}>
        <div className="content-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3>Items</h3>
            {isLoading && <span className="loading-spinner">⟳ Loading…</span>}
          </div>
          <div className="table-container">
            <table className="activities-table">
              <thead>
                <tr>
                  {['S.No','Name','Rate','Description','SKU','Product Type','Account','GST Rate','HSN Code','Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {tableData.length > 0 ? tableData.map(r => (
                  <tr key={r.sNo}>
                    <td>{r.sNo}</td><td>{r.name}</td><td>{r.rate}</td>
                    <td>{r.description}</td><td>{r.sku}</td><td>{r.product_type}</td>
                    <td>{r.account}</td><td>{r.gst_rate}</td><td>{r.hsn_code}</td>
                    <td><span className={`status ${r.status.toLowerCase()}`}>{r.status}</span></td>
                  </tr>
                )) : (
                  <tr><td colSpan="10" style={{ textAlign: 'center', padding: 40 }}>
                    {isLoading ? 'Loading…' : <div className="no-data"><div className="no-data-icon">📦</div><p>No items found</p></div>}
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