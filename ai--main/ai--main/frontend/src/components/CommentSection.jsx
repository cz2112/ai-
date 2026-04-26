import { useEffect, useState } from 'react';

import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import getApiErrorMessage from '../services/errorMessage';


export default function CommentSection({ uploadId }) {
  const { user } = useAuth();
  const [comments, setComments] = useState([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const loadComments = async () => {
    setError('');
    try {
      const res = await api.get(`/share/${uploadId}/comments`);
      setComments(res.data || []);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load comments'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    loadComments();
  }, [uploadId]);

  const submitComment = async (e) => {
    e.preventDefault();
    const content = draft.trim();
    if (!content) return;

    setSubmitting(true);
    setError('');
    try {
      const res = await api.post(`/share/${uploadId}/comments`, { content });
      setComments((prev) => [...prev, res.data]);
      setDraft('');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to post comment'));
    } finally {
      setSubmitting(false);
    }
  };

  const deleteComment = async (commentId) => {
    setError('');
    try {
      await api.delete(`/share/comments/${commentId}`);
      setComments((prev) => prev.filter((comment) => comment.id !== commentId));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to delete comment'));
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between gap-3 mb-4">
        <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Comments</h3>
        <button
          onClick={loadComments}
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 p-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={submitComment} className="mb-5">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={3}
          placeholder="Add a comment..."
          className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        />
        <div className="flex justify-end mt-3">
          <button
            type="submit"
            disabled={submitting || !draft.trim()}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {submitting ? 'Posting...' : 'Post Comment'}
          </button>
        </div>
      </form>

      {loading ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">Loading comments...</p>
      ) : comments.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">No comments yet.</p>
      ) : (
        <div className="space-y-3">
          {comments.map((comment) => (
            <div key={comment.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between gap-3 mb-2">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{comment.username || `User #${comment.user_id}`}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{new Date(comment.created_at).toLocaleString()}</p>
                </div>
                {user?.id === comment.user_id && (
                  <button
                    onClick={() => deleteComment(comment.id)}
                    className="text-xs text-red-600 dark:text-red-400 hover:underline"
                  >
                    Delete
                  </button>
                )}
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{comment.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
