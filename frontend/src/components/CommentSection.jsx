import { useState, useEffect } from 'react';
import api from '../services/api';

export default function CommentSection({ uploadId }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchComments();
  }, [uploadId]);

  const fetchComments = async () => {
    try {
      const res = await api.get(`/share/${uploadId}/comments`);
      setComments(res.data);
    } catch {}
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    setLoading(true);
    try {
      await api.post(`/share/${uploadId}/comments`, { content: newComment.trim() });
      setNewComment('');
      fetchComments();
    } catch {}
    setLoading(false);
  };

  const handleDelete = async (commentId) => {
    try {
      await api.delete(`/share/comments/${commentId}`);
      fetchComments();
    } catch {}
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
        Comments ({comments.length})
      </h3>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
          className="flex-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400"
        />
        <button
          type="submit"
          disabled={loading || !newComment.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition"
        >
          Post
        </button>
      </form>

      <div className="space-y-3">
        {comments.map((c) => (
          <div key={c.id} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{c.username}</span>
                <span className="text-xs text-gray-400 dark:text-gray-500 ml-2">
                  {new Date(c.created_at).toLocaleString()}
                </span>
              </div>
              <button
                onClick={() => handleDelete(c.id)}
                className="text-xs text-gray-400 hover:text-red-500"
              >
                Delete
              </button>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{c.content}</p>
          </div>
        ))}
        {comments.length === 0 && (
          <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-4">No comments yet</p>
        )}
      </div>
    </div>
  );
}
