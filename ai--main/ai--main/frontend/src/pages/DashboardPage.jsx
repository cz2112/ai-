import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api from '../services/api';
import getApiErrorMessage from '../services/errorMessage';

const STATUS_COLORS = {
  Pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  Processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  Completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  Failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export default function DashboardPage() {
  const coursesAvailable = true;
  const [uploads, setUploads] = useState([]);
  const [courses, setCourses] = useState([]);
  const [file, setFile] = useState(null);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterCourse, setFilterCourse] = useState('');
  const [sort, setSort] = useState('-created_at');
  const [newCourse, setNewCourse] = useState('');
  const [selectedCourse, setSelectedCourse] = useState('');
  const [visibilityUpdating, setVisibilityUpdating] = useState({});

  const fetchUploads = useCallback(async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (filterStatus) params.status = filterStatus;
      if (filterCourse) params.course_id = filterCourse;
      if (sort) params.sort = sort;
      const res = await api.get('/uploads/', { params });
      setUploads(res.data);
    } catch {}
  }, [search, filterStatus, filterCourse, sort]);

  const fetchCourses = useCallback(async () => {
    try {
      const res = await api.get('/uploads/courses');
      setCourses(res.data);
    } catch {}
  }, []);

  useEffect(() => {
    fetchUploads();
    const interval = setInterval(fetchUploads, 5000);
    return () => clearInterval(interval);
  }, [fetchUploads]);

  useEffect(() => {
    if (coursesAvailable) {
      fetchCourses();
    }
  }, [fetchCourses, coursesAvailable]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file && files.length === 0) return;
    setUploading(true);
    setError('');
    try {
      if (files.length > 1) {
        // Batch upload
        const formData = new FormData();
        files.forEach((f) => formData.append('files', f));
        if (coursesAvailable && selectedCourse) formData.append('course_id', selectedCourse);
        await api.post('/uploads/batch', formData);
      } else {
        const formData = new FormData();
        formData.append('file', file || files[0]);
        if (coursesAvailable && selectedCourse) formData.append('course_id', selectedCourse);
        await api.post('/uploads/', formData);
      }
      setFile(null);
      setFiles([]);
      e.target.reset();
      fetchUploads();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Upload failed'));
    } finally {
      setUploading(false);
    }
  };

  const handleAddCourse = async (e) => {
    e.preventDefault();
    if (!newCourse.trim()) return;
    try {
      await api.post('/uploads/courses', { name: newCourse.trim() });
      setNewCourse('');
      fetchCourses();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to add course'));
    }
  };

  const handleDeleteCourse = async (id) => {
    if (!confirm('Delete this course?')) return;
    try {
      await api.delete(`/uploads/courses/${id}`);
      if (filterCourse === String(id)) setFilterCourse('');
      if (selectedCourse === String(id)) setSelectedCourse('');
      fetchCourses();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to delete course'));
    }
  };

  const handleRetry = async (id) => {
    await api.post(`/uploads/${id}/retry`);
    fetchUploads();
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this upload?')) return;
    await api.delete(`/uploads/${id}`);
    fetchUploads();
  };

  const handleVisibilityChange = async (id, isShared) => {
    setError('');
    setVisibilityUpdating((prev) => ({ ...prev, [id]: true }));
    try {
      await api.patch(`/share/uploads/${id}/visibility`, { is_shared: isShared });
      setUploads((prev) =>
        prev.map((upload) =>
          upload.id === id ? { ...upload, is_shared: isShared } : upload
        )
      );
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to update file visibility'));
    } finally {
      setVisibilityUpdating((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  const getCourseName = (upload) =>
    upload.course_name || courses.find((course) => course.id === upload.course_id)?.name || '';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Upload Section */}
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Upload Study Material</h2>
          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 p-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}
          <form onSubmit={handleUpload} className="flex gap-4 items-end flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">
                Select files (PDF, PPTX, DOCX, MP3, WAV, MP4, MOV, PNG, JPG)
              </label>
              <input
                type="file"
                accept=".pdf,.mp3,.wav,.mp4,.mov,.pptx,.ppt,.docx,.png,.jpg,.jpeg"
                multiple
                onChange={(e) => {
                  const selected = Array.from(e.target.files);
                  setFiles(selected);
                  setFile(selected[0] || null);
                }}
                className="w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-600 file:font-medium hover:file:bg-blue-100 dark:file:bg-blue-900 dark:file:text-blue-300 dark:text-gray-300"
              />
            </div>
            {coursesAvailable && (
              <div className="min-w-[160px]">
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">Course (optional)</label>
                <select
                  value={selectedCourse}
                  onChange={(e) => setSelectedCourse(e.target.value)}
                  className="w-full text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value="">No course</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
            )}
            <button
              type="submit"
              disabled={(!file && files.length === 0) || uploading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
            >
              {uploading ? 'Uploading...' : files.length > 1 ? `Upload ${files.length} files` : 'Upload'}
            </button>
          </form>
        </div>

        {coursesAvailable && (
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 mb-6">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Courses:</span>
              {courses.map((c) => (
                <span key={c.id} className="inline-flex items-center gap-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs px-3 py-1 rounded-full">
                  {c.name}
                  <button
                    onClick={() => handleDeleteCourse(c.id)}
                    className="ml-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400"
                    title="Delete course"
                  >
                    x
                  </button>
                </span>
              ))}
              <form onSubmit={handleAddCourse} className="inline-flex items-center gap-2 ml-auto">
                <input
                  type="text"
                  value={newCourse}
                  onChange={(e) => setNewCourse(e.target.value)}
                  placeholder="New course..."
                  className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400"
                />
                <button
                  type="submit"
                  className="text-sm bg-green-600 text-white px-3 py-1 rounded-lg hover:bg-green-700 transition"
                >
                  Add
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Search / Filter / Sort Controls */}
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 mb-6">
          <div className="flex gap-3 flex-wrap items-center">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search uploads..."
              className="flex-1 min-w-[180px] text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400"
            />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="">All statuses</option>
              <option value="Pending">Pending uploads</option>
              <option value="Processing">Processing uploads</option>
              <option value="Completed">Completed uploads</option>
              <option value="Failed">Failed uploads</option>
            </select>
            {coursesAvailable && (
              <select
                value={filterCourse}
                onChange={(e) => setFilterCourse(e.target.value)}
                className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="">All courses</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            )}
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="-created_at">Newest first</option>
              <option value="created_at">Oldest first</option>
              <option value="filename">Name A-Z</option>
              <option value="-filename">Name Z-A</option>
            </select>
          </div>
        </div>

        {/* Uploads List */}
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Your Uploads</h2>
        {uploads.length === 0 ? (
          <p className="text-gray-400 dark:text-gray-500 text-center py-12">No uploads yet. Upload a file to get started.</p>
        ) : (
          <div className="space-y-3">
            {uploads.map((u) => (
              <div key={u.id} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <Link to={`/uploads/${u.id}`} className="font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 truncate block">
                    {u.filename}
                  </Link>
                  <div className="flex gap-3 text-xs text-gray-400 dark:text-gray-500 mt-1">
                    <span>{u.file_type.toUpperCase()}</span>
                    <span>{formatSize(u.file_size)}</span>
                    <span>{new Date(u.created_at).toLocaleString()}</span>
                    {getCourseName(u) && <span className="text-blue-500 dark:text-blue-400">{getCourseName(u)}</span>}
                  </div>
                  {u.status === 'Failed' && u.error_message && (
                    <p className="mt-2 text-xs text-red-600 dark:text-red-400 break-words">
                      {u.error_message}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-3 ml-4">
                  {u.status === 'Completed' && (
                    <div className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden shrink-0">
                      <button
                        type="button"
                        onClick={() => handleVisibilityChange(u.id, false)}
                        disabled={Boolean(visibilityUpdating[u.id]) || !u.is_shared}
                        className={`px-3 py-1.5 text-xs font-medium transition ${
                          !u.is_shared
                            ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
                            : 'bg-white text-gray-600 hover:bg-gray-50 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800'
                        } ${visibilityUpdating[u.id] ? 'opacity-60 cursor-wait' : ''}`}
                        title="Only you and explicitly shared users/groups can access this file"
                      >
                        Private
                      </button>
                      <button
                        type="button"
                        onClick={() => handleVisibilityChange(u.id, true)}
                        disabled={Boolean(visibilityUpdating[u.id]) || Boolean(u.is_shared)}
                        className={`px-3 py-1.5 text-xs font-medium border-l border-gray-300 dark:border-gray-600 transition ${
                          u.is_shared
                            ? 'bg-green-600 text-white'
                            : 'bg-white text-gray-600 hover:bg-gray-50 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800'
                        } ${visibilityUpdating[u.id] ? 'opacity-60 cursor-wait' : ''}`}
                        title="Anyone with access to the shared materials list can open this file"
                      >
                        Public
                      </button>
                    </div>
                  )}
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[u.status]}`}>
                    {u.status}
                  </span>
                  {u.status === 'Failed' && (
                    <button onClick={() => handleRetry(u.id)} className="text-blue-600 dark:text-blue-400 text-xs hover:underline">
                      Retry
                    </button>
                  )}
                  <button onClick={() => handleDelete(u.id)} className="text-red-400 hover:text-red-600 dark:hover:text-red-400 text-xs">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
