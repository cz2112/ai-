import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api from '../services/api';

const STATUS_COLORS = {
  Pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  Processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  Completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  Failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
};

export default function AdminPage() {
  const [tab, setTab] = useState('users');
  const [loading, setLoading] = useState(true);

  // Users state
  const [users, setUsers] = useState([]);

  // Uploads state
  const [uploads, setUploads] = useState([]);
  const [uploadSearch, setUploadSearch] = useState('');
  const [uploadStatusFilter, setUploadStatusFilter] = useState('');

  // Statistics state
  const [stats, setStats] = useState(null);

  // Settings state
  const [settings, setSettings] = useState({
    max_uploads_per_user: 0,
    max_upload_size_mb: 0,
    max_audio_minutes: 0,
    max_pdf_pages: 0,
  });
  const [settingsSaved, setSettingsSaved] = useState(false);

  // Fetch users
  const fetchUsers = useCallback(async () => {
    try {
      const res = await api.get('/admin/users');
      setUsers(res.data);
    } catch {
      /* ignore */
    }
  }, []);

  // Fetch uploads
  const fetchUploads = useCallback(async () => {
    try {
      const params = {};
      if (uploadSearch) params.search = uploadSearch;
      if (uploadStatusFilter) params.status = uploadStatusFilter;
      const res = await api.get('/admin/uploads', { params });
      setUploads(res.data);
    } catch {
      /* ignore */
    }
  }, [uploadSearch, uploadStatusFilter]);

  // Fetch statistics
  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get('/admin/stats');
      setStats(res.data);
    } catch {
      /* ignore */
    }
  }, []);

  // Fetch settings
  const fetchSettings = useCallback(async () => {
    try {
      const res = await api.get('/admin/settings');
      setSettings(res.data);
    } catch {
      /* ignore */
    }
  }, []);

  // Load data based on active tab
  useEffect(() => {
    setLoading(true);
    const load = async () => {
      if (tab === 'users') await fetchUsers();
      else if (tab === 'uploads') await fetchUploads();
      else if (tab === 'statistics') await fetchStats();
      else if (tab === 'settings') await fetchSettings();
      setLoading(false);
    };
    load();
  }, [tab, fetchUsers, fetchUploads, fetchStats, fetchSettings]);

  // Re-fetch uploads when filters change
  useEffect(() => {
    if (tab === 'uploads') {
      fetchUploads();
    }
  }, [uploadSearch, uploadStatusFilter, tab, fetchUploads]);

  // User actions
  const handleToggleUser = async (id) => {
    try {
      await api.patch(`/admin/users/${id}/toggle`);
      fetchUsers();
    } catch {
      /* ignore */
    }
  };

  const handleDeleteUser = async (id) => {
    if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
    try {
      await api.delete(`/admin/users/${id}`);
      fetchUsers();
    } catch {
      /* ignore */
    }
  };

  // Upload actions
  const handleDeleteUpload = async (id) => {
    if (!window.confirm('Are you sure you want to delete this upload?')) return;
    try {
      await api.delete(`/admin/uploads/${id}`);
      fetchUploads();
    } catch {
      /* ignore */
    }
  };

  const handleToggleShare = async (id) => {
    try {
      await api.patch(`/admin/uploads/${id}/toggle-share`);
      fetchUploads();
    } catch {
      /* ignore */
    }
  };

  // Settings actions
  const handleSaveSettings = async (e) => {
    e.preventDefault();
    try {
      await api.patch('/admin/settings', settings);
      setSettingsSaved(true);
      setTimeout(() => setSettingsSaved(false), 3000);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Admin Dashboard</h1>

        {/* Tabs */}
        <div className="flex gap-1 bg-white dark:bg-gray-900 rounded-xl shadow-sm p-1 mb-6">
          {['users', 'uploads', 'statistics', 'settings'].map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
                tab === t ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
              }`}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <p className="text-gray-400 dark:text-gray-500">Loading...</p>
          </div>
        ) : (
          <>
            {/* ===== USERS TAB ===== */}
            {tab === 'users' && (
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Username</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Email</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Uploads</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Status</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Joined</th>
                        <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id} className="border-b border-gray-100 dark:border-gray-800 last:border-0">
                          <td className="px-4 py-3 text-gray-900 dark:text-gray-100">
                            <span className="font-medium">{user.username}</span>
                            {user.is_admin && (
                              <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300 font-medium">
                                Admin
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{user.email}</td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{user.upload_count}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                              user.is_active
                                ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                            }`}>
                              {user.is_active ? 'Active' : 'Disabled'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                            {new Date(user.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleToggleUser(user.id)}
                                className={`px-3 py-1 text-xs rounded-lg font-medium transition ${
                                  user.is_active
                                    ? 'bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50'
                                    : 'bg-green-50 text-green-600 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50'
                                }`}
                              >
                                {user.is_active ? 'Disable' : 'Enable'}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(user.id)}
                                className="px-3 py-1 text-xs rounded-lg font-medium bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50 transition"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {users.length === 0 && (
                  <p className="text-gray-400 dark:text-gray-500 text-center py-12">No users found.</p>
                )}
              </div>
            )}

            {/* ===== UPLOADS TAB ===== */}
            {tab === 'uploads' && (
              <div>
                {/* Search and filter controls */}
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 mb-4">
                  <div className="flex gap-3 flex-wrap items-center">
                    <input
                      type="text"
                      value={uploadSearch}
                      onChange={(e) => setUploadSearch(e.target.value)}
                      placeholder="Search uploads..."
                      className="flex-1 min-w-[180px] text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400"
                    />
                    <select
                      value={uploadStatusFilter}
                      onChange={(e) => setUploadStatusFilter(e.target.value)}
                      className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    >
                      <option value="">All statuses</option>
                      <option value="Pending">Pending</option>
                      <option value="Processing">Processing</option>
                      <option value="Completed">Completed</option>
                      <option value="Failed">Failed</option>
                    </select>
                  </div>
                </div>

                {/* Uploads table */}
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Filename</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Type</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Size</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">User</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Status</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Shared</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Date</th>
                          <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {uploads.map((upload) => (
                          <tr key={upload.id} className="border-b border-gray-100 dark:border-gray-800 last:border-0">
                            <td className="px-4 py-3 text-gray-900 dark:text-gray-100 font-medium max-w-[240px]">
                              <Link
                                to={`/uploads/${upload.id}`}
                                className="block truncate hover:text-blue-600 dark:hover:text-blue-400"
                                title={upload.filename}
                              >
                                {upload.filename}
                              </Link>
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400 uppercase">
                              {upload.file_type}
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {formatSize(upload.file_size)}
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {upload.username}
                            </td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${STATUS_COLORS[upload.status] || ''}`}>
                                {upload.status}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <button
                                onClick={() => handleToggleShare(upload.id)}
                                className={`px-2 py-0.5 text-xs rounded-full font-medium transition ${
                                  upload.is_shared
                                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800'
                                    : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                                }`}
                              >
                                {upload.is_shared ? 'Shared' : 'Closed'}
                              </button>
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {new Date(upload.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <Link
                                  to={`/uploads/${upload.id}`}
                                  className="px-3 py-1 text-xs rounded-lg font-medium bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50 transition"
                                >
                                  Open
                                </Link>
                                <button
                                  onClick={() => handleDeleteUpload(upload.id)}
                                  className="px-3 py-1 text-xs rounded-lg font-medium bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50 transition"
                                >
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {uploads.length === 0 && (
                    <p className="text-gray-400 dark:text-gray-500 text-center py-12">No uploads found.</p>
                  )}
                </div>
              </div>
            )}

            {/* ===== STATISTICS TAB ===== */}
            {tab === 'statistics' && stats && (
              <div>
                {/* Stat cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                  <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Users</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.total_users}</p>
                  </div>
                  <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Uploads</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.total_uploads}</p>
                  </div>
                  <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Storage</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.total_storage_mb.toFixed(1)} MB</p>
                  </div>
                </div>

                {/* Uploads by status */}
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6 mb-6">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Uploads by Status</h2>
                  <div className="space-y-3">
                    {Object.entries(stats.uploads_by_status || {}).map(([status, count]) => {
                      const dotColors = {
                        Pending: 'bg-yellow-400',
                        Processing: 'bg-blue-400',
                        Completed: 'bg-green-400',
                        Failed: 'bg-red-400',
                      };
                      return (
                        <div key={status} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={`w-2.5 h-2.5 rounded-full ${dotColors[status] || 'bg-gray-400'}`} />
                            <span className="text-sm text-gray-700 dark:text-gray-300">{status}</span>
                          </div>
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{count}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Recent users */}
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Recent Users</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Username</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Email</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Joined</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(stats.recent_users || []).map((user) => (
                          <tr key={user.id} className="border-b border-gray-100 dark:border-gray-800 last:border-0">
                            <td className="px-4 py-3 text-gray-900 dark:text-gray-100 font-medium">{user.username}</td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{user.email}</td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {new Date(user.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {(stats.recent_users || []).length === 0 && (
                    <p className="text-gray-400 dark:text-gray-500 text-center py-12">No recent users.</p>
                  )}
                </div>
              </div>
            )}

            {/* ===== SETTINGS TAB ===== */}
            {tab === 'settings' && (
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">Platform Settings</h2>

                {settingsSaved && (
                  <div className="bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 p-3 rounded-lg mb-6 text-sm">
                    Settings saved successfully.
                  </div>
                )}

                <form onSubmit={handleSaveSettings} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Max Uploads Per User
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={settings.max_uploads_per_user}
                      onChange={(e) => setSettings({ ...settings, max_uploads_per_user: parseInt(e.target.value, 10) || 0 })}
                      className="w-full max-w-xs text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Max File Size (MB)
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={settings.max_upload_size_mb}
                      onChange={(e) => setSettings({ ...settings, max_upload_size_mb: parseInt(e.target.value, 10) || 0 })}
                      className="w-full max-w-xs text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Max Audio Minutes
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={settings.max_audio_minutes}
                      onChange={(e) => setSettings({ ...settings, max_audio_minutes: parseInt(e.target.value, 10) || 0 })}
                      className="w-full max-w-xs text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Max PDF Pages
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={settings.max_pdf_pages}
                      onChange={(e) => setSettings({ ...settings, max_pdf_pages: parseInt(e.target.value, 10) || 0 })}
                      className="w-full max-w-xs text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <button
                    type="submit"
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition font-medium text-sm"
                  >
                    Save Settings
                  </button>
                </form>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
