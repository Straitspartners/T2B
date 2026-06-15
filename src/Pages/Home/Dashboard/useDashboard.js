import { useState, useEffect, useCallback } from 'react';

const BASE_URL = 'http://127.0.0.1:8000/api';

// ✅ Single source of truth for auth token - checks both sessionStorage and localStorage
export const getAuthToken = () => {
  return sessionStorage.getItem('authToken') || localStorage.getItem('authToken') || null;
};

export const getUserName = () => {
  try {
    return (
      JSON.parse(localStorage.getItem('userData') || '{}')?.name ||
      localStorage.getItem('userName') ||
      'User'
    );
  } catch {
    return 'User';
  }
};

// ✅ Generic dashboard hook — pass in endpoint and a transform function
export function useDashboard(endpoint, transformFn, dataKey) {
  const [stats, setStats] = useState({
    dataFetchedFromTally: 0,
    dataMigratedToZoho: 0,
    pendingMigration: 0,
    loading: true,
  });
  const [tableData, setTableData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [alert, setAlert] = useState({ show: false, type: '', message: '' });

  const showAlert = (type, message) => setAlert({ show: true, type, message });
  const hideAlert = () => setAlert({ show: false, type: '', message: '' });

  const fetchData = useCallback(async () => {
    try {
      const authToken = getAuthToken();
      if (!authToken) throw new Error('Authentication token not found. Please login again.');

      const response = await fetch(`${BASE_URL}/${endpoint}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`, // ✅ Consistent Token auth across all pages
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Request failed (${response.status}): ${errorText}`);
      }

      const data = await response.json();

      const fetched = data.summary?.fetched_from_tally || 0;
      const pushed = data.summary?.pushed_to_zoho || 0;

      setStats({
        dataFetchedFromTally: fetched,
        dataMigratedToZoho: pushed,
        pendingMigration: data.summary?.pending_to_push_to_zoho ?? (fetched - pushed),
        loading: false,
      });

      const rawList = data[dataKey] || [];
      setTableData(transformFn(rawList));
      setIsLoading(false);
      hideAlert();
    } catch (error) {
      showAlert('error', error.message);
      setStats(prev => ({ ...prev, loading: false }));
      setIsLoading(false);
    }
  }, [endpoint, dataKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 30000); // ✅ 30s interval (was 10s — too aggressive)
    return () => clearInterval(id);
  }, [fetchData]);

  const refresh = () => {
    setStats(prev => ({ ...prev, loading: true }));
    setIsLoading(true);
    hideAlert();
    fetchData();
  };

  return { stats, tableData, isLoading, alert, hideAlert, refresh };
}

// ✅ Helpers
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric', month: 'short', day: '2-digit',
    });
  } catch {
    return dateString;
  }
};

export const formatAmount = (amount) => {
  if (amount === null || amount === undefined || amount === 'N/A' || amount === '') return 'N/A';
  const num = parseFloat(amount);
  if (isNaN(num)) return amount;
  return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
};