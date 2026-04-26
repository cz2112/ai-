import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import Navbar from '../components/Navbar';
import api from '../services/api';
import getApiErrorMessage from '../services/errorMessage';


const formatShareType = (share) => {
  if (share.group_id) return 'Group';
  if (share.shared_with) return 'Direct';
  return 'Public';
};


export default function SharedPage() {
  const [shares, setShares] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadShares = async () => {
    setError('');
    try {
      const res = await api.get('/share/shared-with-me');
      setShares(res.data || []);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load shared materials'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadShares();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Shared With Me</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Direct shares, public materials, and files shared into your groups.</p>
          </div>
          <button
            onClick={loadShares}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
          >
            Refresh
          </button>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 p-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-8 text-sm text-gray-500 dark:text-gray-400">
            Loading shared materials...
          </div>
        ) : shares.length === 0 ? (
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-8 text-sm text-gray-500 dark:text-gray-400">
            Nothing has been shared with you yet.
          </div>
        ) : (
          <div className="space-y-4">
            {shares.map((share, index) => (
              <div key={`${share.id}-${share.upload_id}-${index}`} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">{share.filename || `Upload #${share.upload_id}`}</h2>
                  <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                    {formatShareType(share)}
                  </span>
                </div>
                <div className="flex flex-wrap gap-4 text-sm text-gray-500 dark:text-gray-400">
                  <span>Owner: {share.owner_name || 'Unknown'}</span>
                  <span>Upload ID: {share.upload_id}</span>
                  <span>Permission: {share.permission || 'read'}</span>
                  {share.group_name && <span>Group: {share.group_name}</span>}
                  <span>{new Date(share.created_at).toLocaleString()}</span>
                </div>
                {share.message && (
                  <p className="mt-3 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{share.message}</p>
                )}
                <div className="mt-4">
                  <Link
                    to={`/uploads/${share.upload_id}`}
                    className="inline-flex items-center px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition"
                  >
                    Open Analysis
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
