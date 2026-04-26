import { useState, useEffect, useRef } from 'react';
import api from '../services/api';

export default function ChatPanel({ uploadId }) {
  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchConversations();
  }, [uploadId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const res = await api.get(`/chat/${uploadId}/conversations`);
      setConversations(res.data);
    } catch {}
  };

  const loadConversation = async (convId) => {
    try {
      const res = await api.get(`/chat/${uploadId}/conversations/${convId}`);
      setActiveConv(res.data);
      setMessages(res.data.messages || []);
    } catch {}
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    setLoading(true);
    const userMsg = { role: 'user', content: input, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    try {
      const res = await api.post(`/chat/${uploadId}`, {
        message: input,
        conversation_id: activeConv?.id || null,
      });
      if (!activeConv) {
        fetchConversations();
        // Set active conv from response
        const convRes = await api.get(`/chat/${uploadId}/conversations`);
        if (convRes.data.length > 0) {
          setActiveConv(convRes.data[0]);
        }
      }
      setMessages((prev) => [...prev, res.data]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error: Failed to get response', created_at: new Date().toISOString() }]);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    setActiveConv(null);
    setMessages([]);
  };

  const deleteConversation = async (convId) => {
    try {
      await api.delete(`/chat/${uploadId}/conversations/${convId}`);
      if (activeConv?.id === convId) {
        setActiveConv(null);
        setMessages([]);
      }
      fetchConversations();
    } catch {}
  };

  return (
    <div className="flex h-[500px] border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      {/* Sidebar */}
      <div className="w-48 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex flex-col">
        <button
          onClick={startNewChat}
          className="m-2 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
        >
          + New Chat
        </button>
        <div className="flex-1 overflow-y-auto">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`px-3 py-2 text-sm cursor-pointer flex justify-between items-center hover:bg-gray-100 dark:hover:bg-gray-700 ${
                activeConv?.id === c.id ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'
              }`}
              onClick={() => loadConversation(c.id)}
            >
              <span className="truncate flex-1">{c.title}</span>
              <button
                onClick={(e) => { e.stopPropagation(); deleteConversation(c.id); }}
                className="ml-1 text-gray-400 hover:text-red-500 text-xs"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <p className="text-gray-400 dark:text-gray-500 text-center mt-20 text-sm">
              Ask a question about this study material...
            </p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-700 px-4 py-2 rounded-2xl text-sm text-gray-500">
                Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={sendMessage} className="border-t border-gray-200 dark:border-gray-700 p-3 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
            className="flex-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
