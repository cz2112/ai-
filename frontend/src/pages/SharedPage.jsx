import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api from '../services/api';

export default function SharedPage() {
  const [shares, setShares] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchShares();
  }, []);

  const fetchShares = async () => {
    try {
      const res = await api.get('/share/shared-with-me');
      setShares(res.data);
    } catch {}
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Shared With Me</h1>

        {loading ? (
          <p className="text-gray-400 text-center py-12">Loading...</p>
        ) : shares.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 dark:text-gray-500">No shared materials yet.</p>
            <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
              When someone shares study materials with you, they will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {shares.map((s) => (
              <div key={`${s.id}-${s.upload_id}`} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <Link
                    to={`/uploads/${s.upload_id}`}
                    className="font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 truncate block"
                  >
                    {s.filename}
                  </Link>
                  <div className="flex gap-3 text-xs text-gray-400 dark:text-gray-500 mt-1">
                    <span>Shared by: {s.owner_name}</span>
                    <span>{new Date(s.created_at).toLocaleString()}</span>
                  </div>
                  {s.message && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 italic">"{s.message}"</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
