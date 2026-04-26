import { useEffect, useState } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import Navbar from '../components/Navbar';
import StudyHeatmap from '../components/StudyHeatmap';
import api from '../services/api';
import getApiErrorMessage from '../services/errorMessage';


const COLORS = ['#3b82f6', '#22c55e', '#eab308', '#ef4444'];

const EMPTY_STATS = {
  total_uploads: 0,
  completed_uploads: 0,
  total_flashcards: 0,
  known_flashcards: 0,
  total_concepts: 0,
  uploads_by_date: [],
  uploads_by_status: {},
  study_activity_by_date: [],
};

const EMPTY_QUOTA = {
  uploads_used: 0,
  uploads_limit: 0,
  max_file_size_mb: 0,
  max_audio_minutes: 0,
  max_pdf_pages: 0,
};


export default function StatsPage() {
  const [stats, setStats] = useState(null);
  const [quota, setQuota] = useState(null);
  const [heatmapData, setHeatmapData] = useState([]);
  const [learningPath, setLearningPath] = useState(null);
  const [pathUploadId, setPathUploadId] = useState('');
  const [pathLoading, setPathLoading] = useState(false);
  const [uploads, setUploads] = useState([]);
  const [progressData, setProgressData] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setError('');

      const [statsRes, quotaRes, uploadsRes] = await Promise.allSettled([
        api.get('/uploads/stats'),
        api.get('/uploads/quota'),
        api.get('/uploads/'),
      ]);

      const statsData = statsRes.status === 'fulfilled' ? statsRes.value.data : EMPTY_STATS;
      const quotaData = quotaRes.status === 'fulfilled' ? quotaRes.value.data : EMPTY_QUOTA;
      const uploadsData = uploadsRes.status === 'fulfilled' ? uploadsRes.value.data : [];

      setStats(statsData);
      setQuota(quotaData);
      setUploads((uploadsData || []).filter((up) => up.status === 'Completed'));
      setHeatmapData(statsData.study_activity_by_date || []);

      let cumulative = 0;
      setProgressData((statsData.uploads_by_date || []).map((d) => {
        cumulative += d.count;
        return { date: d.date, uploads: d.count, total: cumulative };
      }));

      const rejected = [statsRes, quotaRes, uploadsRes].find((result) => result.status === 'rejected');
      if (rejected) {
        setError(getApiErrorMessage(rejected.reason, 'Some statistics are unavailable right now.'));
      }
    };

    load();
  }, []);

  const loadLearningPath = async () => {
    if (!pathUploadId) return;
    setPathLoading(true);
    try {
      const res = await api.get('/uploads/learning-path/recommend', { params: { upload_id: pathUploadId } });
      setLearningPath(res.data);
    } catch {
      setLearningPath(null);
    }
    setPathLoading(false);
  };

  const forgettingCurveData = [];
  for (let day = 0; day <= 30; day++) {
    const noReview = Math.round(100 * Math.exp(-0.3 * day));
    const withSm2 = Math.round(Math.min(100, 100 * Math.exp(-0.05 * day) + 15 * Math.sin(day * 0.5) * Math.exp(-0.1 * day)));
    forgettingCurveData.push({ day: `Day ${day}`, noReview, withSm2: Math.max(withSm2, 20) });
  }

  if (!stats || !quota) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <Navbar />
        <p className="text-center text-gray-400 py-20">Loading...</p>
      </div>
    );
  }

  const statusData = Object.entries(stats.uploads_by_status || {}).map(([name, value]) => ({ name, value }));
  const fcPercent = stats.total_flashcards > 0 ? Math.round((stats.known_flashcards / stats.total_flashcards) * 100) : 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <h2 className="text-lg font-semibold mb-6 dark:text-white">Learning Statistics</h2>

        {error && (
          <div className="bg-yellow-50 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200 rounded-lg p-3 text-sm mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Uploads', value: stats.total_uploads },
            { label: 'Completed', value: stats.completed_uploads },
            { label: 'Flashcards Mastered', value: `${stats.known_flashcards}/${stats.total_flashcards}` },
            { label: 'Key Concepts', value: stats.total_concepts },
          ].map((c) => (
            <div key={c.label} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5 text-center">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{c.value}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{c.label}</p>
            </div>
          ))}
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5 mb-8">
          <h3 className="text-sm font-semibold mb-4 dark:text-white">Study Activity</h3>
          <StudyHeatmap data={heatmapData} />
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
            <h3 className="text-sm font-semibold mb-4 dark:text-white">Uploads Over Time</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={stats.uploads_by_date || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
            <h3 className="text-sm font-semibold mb-4 dark:text-white">Status Distribution</h3>
            {statusData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                    {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-10">No data</p>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
            <h3 className="text-sm font-semibold mb-4 dark:text-white">Learning Progress</h3>
            {progressData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={progressData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="total" stroke="#3b82f6" strokeWidth={2} dot={false} name="Cumulative" />
                  <Line type="monotone" dataKey="uploads" stroke="#22c55e" strokeWidth={2} dot={false} name="Daily" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-10">No data yet</p>
            )}
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
            <h3 className="text-sm font-semibold mb-4 dark:text-white">Forgetting Curve (Ebbinghaus)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={forgettingCurveData.filter((_, i) => i % 3 === 0)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area type="monotone" dataKey="noReview" stroke="#ef4444" fill="#ef444420" strokeWidth={2} name="Without Review" />
                <Area type="monotone" dataKey="withSm2" stroke="#22c55e" fill="#22c55e20" strokeWidth={2} name="With SM-2 Review" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5 mb-8">
          <h3 className="text-sm font-semibold mb-3 dark:text-white">Flashcard Mastery</h3>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
            <div className="bg-green-500 h-4 rounded-full transition-all" style={{ width: `${fcPercent}%` }} />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">{fcPercent}% mastered ({stats.known_flashcards} of {stats.total_flashcards})</p>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5 mb-8">
          <h3 className="text-sm font-semibold mb-4 dark:text-white">AI Learning Path</h3>
          <div className="flex gap-2 mb-4">
            <select value={pathUploadId} onChange={(e) => setPathUploadId(e.target.value)} className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg p-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
              <option value="">Select a material...</option>
              {uploads.map((u) => (
                <option key={u.id} value={u.id}>{u.filename}</option>
              ))}
            </select>
            <button onClick={loadLearningPath} disabled={!pathUploadId || pathLoading} className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition disabled:opacity-50">
              {pathLoading ? 'Generating...' : 'Generate'}
            </button>
          </div>
          {learningPath && learningPath.steps && (
            <div className="space-y-3">
              {learningPath.steps.map((step, i) => (
                <div key={i} className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-sm font-bold">{i + 1}</div>
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">{step.title}</h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{step.description}</p>
                    {step.resources && (
                      <p className="text-xs text-blue-500 dark:text-blue-400 mt-1">Resources: {step.resources}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
          {learningPath && !learningPath.steps && (
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{JSON.stringify(learningPath, null, 2)}</p>
          )}
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
          <h3 className="text-sm font-semibold mb-3 dark:text-white">Usage Quota</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500 dark:text-gray-400">Uploads</p>
              <p className="font-medium dark:text-white">{quota.uploads_used} / {quota.uploads_limit}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">Max File Size</p>
              <p className="font-medium dark:text-white">{quota.max_file_size_mb} MB</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">Max Audio</p>
              <p className="font-medium dark:text-white">{quota.max_audio_minutes} min</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">Max PDF Pages</p>
              <p className="font-medium dark:text-white">{quota.max_pdf_pages}</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
