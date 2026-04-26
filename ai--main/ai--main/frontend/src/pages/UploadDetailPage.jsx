import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import Navbar from '../components/Navbar';
import ChatPanel from '../components/ChatPanel';
import KnowledgeGraph from '../components/KnowledgeGraph';
import CommentSection from '../components/CommentSection';
import { useAuth } from '../contexts/AuthContext';
import getApiErrorMessage from '../services/errorMessage';

export default function UploadDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const sharingAvailable = true;
  const [data, setData] = useState(null);
  const [tab, setTab] = useState('summary');
  const [cardIndex, setCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [reviewMode, setReviewMode] = useState(false);
  const [reviewCards, setReviewCards] = useState([]);
  const [editingSummary, setEditingSummary] = useState(false);
  const [editSummaryText, setEditSummaryText] = useState('');
  const [editingCard, setEditingCard] = useState(null);
  const [editCardQ, setEditCardQ] = useState('');
  const [editCardA, setEditCardA] = useState('');
  const [editingConcept, setEditingConcept] = useState(null);
  const [editConceptTitle, setEditConceptTitle] = useState('');
  const [editConceptDesc, setEditConceptDesc] = useState('');
  const [shareModal, setShareModal] = useState(false);
  const [shareTargetType, setShareTargetType] = useState('direct');
  const [shareUsername, setShareUsername] = useState('');
  const [selectedGroupId, setSelectedGroupId] = useState('');
  const [sharePermission, setSharePermission] = useState('read');
  const [shareNote, setShareNote] = useState('');
  const [shareMsg, setShareMsg] = useState('');
  const [publicShared, setPublicShared] = useState(false);
  const [myGroups, setMyGroups] = useState([]);
  const [existingShares, setExistingShares] = useState([]);
  const [sm2Rating, setSm2Rating] = useState(null);

  useEffect(() => {
    let stopped = false;
    let intervalId = null;
    const load = async () => {
      try {
        const res = await api.get(`/uploads/${id}`);
        if (!stopped) setData(res.data);
        if (res.data.status === 'Completed' || res.data.status === 'Failed') {
          clearInterval(intervalId);
        }
      } catch { /* ignore */ }
    };
    intervalId = setInterval(load, 5000);
    load();
    return () => { stopped = true; clearInterval(intervalId); };
  }, [id]);

  const shuffleArray = (arr) => {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };

  const toggleKnown = async (fcId, known) => {
    if (!user || data?.user_id !== user.id) return;
    await api.patch(`/uploads/flashcards/${fcId}`, { is_known: known });
    setData((prev) => ({
      ...prev,
      flashcards: prev.flashcards.map((f) =>
        f.id === fcId ? { ...f, is_known: known } : f
      ),
    }));
  };

  const toggleReviewMode = () => {
    if (!user || data?.user_id !== user.id) return;
    if (!reviewMode) {
      const unknown = (data.flashcards || []).filter((c) => !c.is_known);
      setReviewCards(shuffleArray(unknown));
      setCardIndex(0);
      setShowAnswer(false);
    } else {
      setCardIndex(0);
      setShowAnswer(false);
    }
    setReviewMode(!reviewMode);
  };

  const saveSummary = async () => {
    if (!user || data?.user_id !== user.id) return;
    await api.patch(`/uploads/summary/${data.summary.id}`, { content: editSummaryText });
    setData((prev) => ({
      ...prev,
      summary: { ...prev.summary, content: editSummaryText },
    }));
    setEditingSummary(false);
  };

  const saveFlashcard = async (fcId) => {
    if (!user || data?.user_id !== user.id) return;
    await api.patch(`/uploads/flashcards/${fcId}`, { question: editCardQ, answer: editCardA });
    setData((prev) => ({
      ...prev,
      flashcards: prev.flashcards.map((f) =>
        f.id === fcId ? { ...f, question: editCardQ, answer: editCardA } : f
      ),
    }));
    setEditingCard(null);
  };

  const saveConcept = async (cId) => {
    if (!user || data?.user_id !== user.id) return;
    await api.patch(`/uploads/concepts/${cId}`, { title: editConceptTitle, description: editConceptDesc });
    setData((prev) => ({
      ...prev,
      key_concepts: prev.key_concepts.map((c) =>
        c.id === cId ? { ...c, title: editConceptTitle, description: editConceptDesc } : c
      ),
    }));
    setEditingConcept(null);
  };

  const loadSharingState = async (uploadData = data) => {
    try {
      const [sharesRes, groupsRes] = await Promise.all([
        api.get('/share/mine', { params: { upload_id: parseInt(id, 10) } }),
        api.get('/share/groups'),
      ]);
      setExistingShares(sharesRes.data || []);
      setMyGroups(groupsRes.data || []);
      if (uploadData) {
        setPublicShared(Boolean(uploadData.is_shared));
      }
    } catch (err) {
      setShareMsg(getApiErrorMessage(err, 'Failed to load share settings'));
    }
  };

  const handleShare = async () => {
    setShareMsg('');
    try {
      if (shareTargetType === 'direct') {
        if (!shareUsername.trim()) {
          setShareMsg('Please enter a username or email.');
          return;
        }
        await api.post('/share/', {
          upload_id: parseInt(id, 10),
          shared_with_username: shareUsername.trim(),
          permission: sharePermission,
          message: shareNote.trim() || null,
        });
      } else if (shareTargetType === 'group') {
        if (!selectedGroupId) {
          setShareMsg('Please select a group.');
          return;
        }
        await api.post('/share/', {
          upload_id: parseInt(id, 10),
          group_id: parseInt(selectedGroupId, 10),
          permission: 'read',
          message: shareNote.trim() || null,
        });
      }
      setShareMsg('Shared successfully.');
      setShareUsername('');
      setSelectedGroupId('');
      setShareNote('');
      await loadSharingState();
    } catch (err) {
      setShareMsg(getApiErrorMessage(err, 'Failed to share'));
    }
  };

  const toggleVisibility = async () => {
    setShareMsg('');
    try {
      const nextValue = !publicShared;
      const res = await api.patch(`/share/uploads/${id}/visibility`, { is_shared: nextValue });
      setPublicShared(Boolean(res.data?.is_shared));
      setData((prev) => ({ ...prev, is_shared: Boolean(res.data?.is_shared) }));
      setShareMsg(nextValue ? 'Visibility updated successfully: this file is now public.' : 'Visibility updated successfully: this file is now private.');
    } catch (err) {
      setShareMsg(getApiErrorMessage(err, 'Failed to update visibility'));
    }
  };

  const removeShare = async (shareId) => {
    setShareMsg('');
    try {
      await api.delete(`/share/${shareId}`);
      setExistingShares((prev) => prev.filter((share) => share.id !== shareId));
    } catch (err) {
      setShareMsg(getApiErrorMessage(err, 'Failed to remove share'));
    }
  };

  const handleSm2Review = async (fcId, quality) => {
    if (!user || data?.user_id !== user.id) return;
    try {
      await api.post(`/uploads/flashcards/${fcId}/review`, { quality });
      setSm2Rating(quality);
      setTimeout(() => {
        setSm2Rating(null);
        setShowAnswer(false);
        setCardIndex((prev) => Math.min(prev + 1, activeCards.length - 1));
      }, 600);
    } catch { /* ignore */ }
  };

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <p className="text-gray-400 dark:text-gray-500">Loading...</p>
      </div>
    );
  }

  const allCards = data.flashcards || [];
  const activeCards = reviewMode ? reviewCards : allCards;
  const currentCard = activeCards[cardIndex];
  const knownCount = allCards.filter((c) => c.is_known).length;
  const isOwner = user?.id === data.user_id;
  const TABS = ['summary', 'concepts', 'flashcards', 'qa', 'graph', 'transcript'];
  const TAB_LABELS = { summary: 'Summary', concepts: 'Concepts', flashcards: 'Flashcards', qa: 'Q&A', graph: 'Graph', transcript: 'Transcript' };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Link to="/" className="text-blue-600 hover:underline text-sm dark:text-blue-400">&larr; Dashboard</Link>
          <h1 className="text-lg font-bold truncate text-gray-900 dark:text-gray-100">{data.filename}</h1>
          {!isOwner && (
            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              Read Only
            </span>
          )}
          <div className="ml-auto flex gap-2">
            {data.status === 'Completed' && (
              <>
                {sharingAvailable && isOwner && (
                  <button onClick={() => { setShareModal(true); loadSharingState(data); }} className="px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 transition">Share</button>
                )}
                <a href={`/api/uploads/${id}/export`} className="px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition" download>Export</a>
              </>
            )}
          </div>
        </div>

        {/* Share Modal */}
        {sharingAvailable && shareModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShareModal(false)}>
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6 w-full max-w-2xl" onClick={(e) => e.stopPropagation()}>
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Share Material</h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-gray-100">Public Visibility</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Public files appear in the shared materials list for other users.</p>
                      </div>
                      <button
                        onClick={toggleVisibility}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition ${publicShared ? 'bg-green-600 text-white hover:bg-green-700' : 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'}`}
                      >
                        {publicShared ? 'Public' : 'Private'}
                      </button>
                    </div>
                  </div>

                  <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setShareTargetType('direct')}
                        className={`px-3 py-1.5 rounded-lg text-sm transition ${shareTargetType === 'direct' ? 'bg-blue-600 text-white' : 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}`}
                      >
                        Direct Share
                      </button>
                      <button
                        onClick={() => setShareTargetType('group')}
                        className={`px-3 py-1.5 rounded-lg text-sm transition ${shareTargetType === 'group' ? 'bg-blue-600 text-white' : 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}`}
                      >
                        Share to Group
                      </button>
                    </div>

                    {shareTargetType === 'direct' ? (
                      <>
                        <input value={shareUsername} onChange={(e) => setShareUsername(e.target.value)} placeholder="Username or email" className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 outline-none" />
                        <select value={sharePermission} onChange={(e) => setSharePermission(e.target.value)} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                          <option value="read">Read Only</option>
                          <option value="edit">Can Edit</option>
                        </select>
                      </>
                    ) : (
                      <select value={selectedGroupId} onChange={(e) => setSelectedGroupId(e.target.value)} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        <option value="">Select a group</option>
                        {myGroups.map((group) => (
                          <option key={group.id} value={group.id}>{group.name}</option>
                        ))}
                      </select>
                    )}

                    <textarea
                      value={shareNote}
                      onChange={(e) => setShareNote(e.target.value)}
                      rows={3}
                      placeholder="Optional note"
                      className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <button onClick={handleShare} className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition">
                      Share Now
                    </button>
                  </div>
                </div>

                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Existing Shares</h4>
                  {existingShares.length === 0 ? (
                    <p className="text-sm text-gray-500 dark:text-gray-400">No direct or group shares yet.</p>
                  ) : (
                    <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
                      {existingShares.map((share) => (
                        <div key={share.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                          <div className="flex items-center justify-between gap-3">
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {share.group_name ? `Group: ${share.group_name}` : share.shared_with ? 'Direct Share' : 'Public Share'}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Permission: {share.permission || 'read'}
                              </p>
                              {share.message && (
                                <p className="text-xs text-gray-600 dark:text-gray-300 mt-2 whitespace-pre-wrap">{share.message}</p>
                              )}
                            </div>
                            <button onClick={() => removeShare(share.id)} className="text-xs text-red-600 dark:text-red-400 hover:underline">
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              {shareMsg && <p className={`text-sm mb-3 ${shareMsg.toLowerCase().includes('failed') || shareMsg.toLowerCase().includes('please') ? 'text-red-600' : 'text-green-600'}`}>{shareMsg}</p>}
              <div className="flex gap-2 justify-end">
                <button onClick={() => setShareModal(false)} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Cancel</button>
              </div>
            </div>
          </div>
        )}

        {/* Status Banner */}
        {data.status !== 'Completed' && (
          <div className={`rounded-xl p-4 mb-6 text-sm ${data.status === 'Processing' ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : data.status === 'Pending' ? 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' : 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300'}`}>
            Status: <strong>{data.status}</strong>
            {data.error_message && <span> &mdash; {data.error_message}</span>}
          </div>
        )}

        {data.status === 'Completed' && (
          <>
            {/* Tabs */}
            <div className="flex gap-1 bg-white dark:bg-gray-900 rounded-xl shadow-sm p-1 mb-6 overflow-x-auto">
              {TABS.map((t) => (
                <button key={t} onClick={() => setTab(t)} className={`flex-1 py-2 rounded-lg text-sm font-medium transition whitespace-nowrap px-3 ${tab === t ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'}`}>
                  {TAB_LABELS[t]}
                </button>
              ))}
            </div>

            {/* Summary Tab */}
            {tab === 'summary' && data.summary && (
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Summary</h2>
                  {isOwner && !editingSummary && (
                    <button onClick={() => { setEditSummaryText(data.summary.content); setEditingSummary(true); }} className="px-3 py-1 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Edit</button>
                  )}
                </div>
                {editingSummary ? (
                  <div>
                    <textarea value={editSummaryText} onChange={(e) => setEditSummaryText(e.target.value)} rows={10} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 outline-none" />
                    <div className="flex gap-2 mt-3">
                      <button onClick={saveSummary} className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition">Save</button>
                      <button onClick={() => setEditingSummary(false)} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Cancel</button>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{data.summary.content}</p>
                )}
              </div>
            )}

            {/* Key Concepts Tab */}
            {tab === 'concepts' && (
              <div className="space-y-3">
                {(data.key_concepts || []).map((c) => (
                  <div key={c.id} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
                    {editingConcept === c.id ? (
                      <div>
                        <input value={editConceptTitle} onChange={(e) => setEditConceptTitle(e.target.value)} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2 text-sm font-semibold text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 outline-none mb-2" />
                        <textarea value={editConceptDesc} onChange={(e) => setEditConceptDesc(e.target.value)} rows={3} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2 text-sm text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 outline-none" />
                        <div className="flex gap-2 mt-3">
                          <button onClick={() => saveConcept(c.id)} className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition">Save</button>
                          <button onClick={() => setEditingConcept(null)} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Cancel</button>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{c.title}</h3>
                          {isOwner && (
                            <button onClick={() => { setEditingConcept(c.id); setEditConceptTitle(c.title); setEditConceptDesc(c.description); }} className="px-3 py-1 text-xs rounded-lg border border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Edit</button>
                          )}
                        </div>
                        <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">{c.description}</p>
                        {c.citation && <blockquote className="mt-3 border-l-4 border-blue-300 dark:border-blue-600 pl-3 text-xs text-gray-500 dark:text-gray-400 italic">{c.citation}</blockquote>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Flashcards Tab */}
            {tab === 'flashcards' && allCards.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Card {activeCards.length > 0 ? cardIndex + 1 : 0} of {activeCards.length} &middot; {knownCount} known of {allCards.length}
                  </div>
                  {isOwner && (
                    <button onClick={toggleReviewMode} className={`px-4 py-2 rounded-lg text-sm font-medium transition ${reviewMode ? 'bg-purple-600 text-white hover:bg-purple-700' : 'border border-purple-300 dark:border-purple-600 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30'}`}>
                      {reviewMode ? 'Exit Review Mode' : 'Review Unknown'}
                    </button>
                  )}
                </div>

                {activeCards.length === 0 && reviewMode && (
                  <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-8 text-center text-gray-500 dark:text-gray-400">All cards are marked as known. Great job!</div>
                )}

                {activeCards.length > 0 && currentCard && (
                  <>
                    {editingCard === currentCard.id ? (
                      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Question</label>
                        <textarea value={editCardQ} onChange={(e) => setEditCardQ(e.target.value)} rows={3} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 outline-none mb-3" />
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Answer</label>
                        <textarea value={editCardA} onChange={(e) => setEditCardA(e.target.value)} rows={3} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 outline-none" />
                        <div className="flex gap-2 mt-3">
                          <button onClick={() => saveFlashcard(currentCard.id)} className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition">Save</button>
                          <button onClick={() => setEditingCard(null)} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Cancel</button>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-8 min-h-[200px] flex flex-col items-center justify-center cursor-pointer relative" onClick={() => setShowAnswer(!showAnswer)}>
                        {isOwner && (
                          <button onClick={(e) => { e.stopPropagation(); setEditingCard(currentCard.id); setEditCardQ(currentCard.question); setEditCardA(currentCard.answer); }} className="absolute top-3 right-3 px-3 py-1 text-xs rounded-lg border border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Edit</button>
                        )}
                        <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">{showAnswer ? 'Answer' : 'Question'}</p>
                        <p className="text-lg text-center font-medium text-gray-900 dark:text-gray-100">{showAnswer ? currentCard.answer : currentCard.question}</p>
                        {!showAnswer && <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">Click to reveal answer</p>}
                      </div>
                    )}

                    {/* SM-2 Rating (shown after revealing answer) */}
                    {isOwner && showAnswer && !editingCard && (
                      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 mt-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 text-center">Rate your recall (SM-2 Spaced Repetition)</p>
                        <div className="flex justify-center gap-2">
                          {[
                            { q: 0, label: 'Forgot', color: 'bg-red-500' },
                            { q: 1, label: 'Hard', color: 'bg-orange-500' },
                            { q: 2, label: 'Struggled', color: 'bg-yellow-500' },
                            { q: 3, label: 'OK', color: 'bg-blue-500' },
                            { q: 4, label: 'Good', color: 'bg-green-500' },
                            { q: 5, label: 'Easy', color: 'bg-emerald-600' },
                          ].map((r) => (
                            <button key={r.q} onClick={(e) => { e.stopPropagation(); handleSm2Review(currentCard.id, r.q); }} className={`px-3 py-1.5 rounded-lg text-white text-xs font-medium transition hover:opacity-80 ${r.color} ${sm2Rating === r.q ? 'ring-2 ring-offset-2 ring-blue-400' : ''}`}>
                              {r.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex justify-center gap-3 mt-4">
                      <button onClick={() => { setCardIndex(Math.max(0, cardIndex - 1)); setShowAnswer(false); }} disabled={cardIndex === 0} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 disabled:opacity-30 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Previous</button>
                      {isOwner && (
                        <button onClick={() => toggleKnown(currentCard.id, !currentCard.is_known)} className={`px-4 py-2 rounded-lg text-sm font-medium transition ${currentCard.is_known ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}`}>
                          {currentCard.is_known ? 'Known' : 'Mark as Known'}
                        </button>
                      )}
                      <button onClick={() => { setCardIndex(Math.min(activeCards.length - 1, cardIndex + 1)); setShowAnswer(false); }} disabled={cardIndex === activeCards.length - 1} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 disabled:opacity-30 hover:bg-gray-50 dark:hover:bg-gray-800 transition">Next</button>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Q&A Tab */}
            {tab === 'qa' && (
              <ChatPanel uploadId={id} />
            )}

            {/* Knowledge Graph Tab */}
            {tab === 'graph' && (
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Knowledge Graph</h2>
                <KnowledgeGraph uploadId={id} />
              </div>
            )}

            {/* Transcript Tab */}
            {tab === 'transcript' && data.transcript && (
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                <h2 className="text-lg font-semibold mb-3 text-gray-900 dark:text-gray-100">Transcript / Extracted Text</h2>
                <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-[500px] overflow-y-auto">{data.transcript}</pre>
              </div>
            )}

            {/* Comment Section */}
            <div className="mt-8">
              <CommentSection uploadId={id} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
