import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

export default function StudyGroupPage() {
  const { user } = useAuth();
  const location = useLocation();
  const [myGroups, setMyGroups] = useState([]);
  const [allGroups, setAllGroups] = useState([]);
  const [tab, setTab] = useState('my');
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newJoinMode, setNewJoinMode] = useState('open');
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [members, setMembers] = useState([]);
  const [joinRequests, setJoinRequests] = useState([]);
  const [inviteInput, setInviteInput] = useState('');
  const [myInvites, setMyInvites] = useState([]);
  const [msg, setMsg] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [groupPanel, setGroupPanel] = useState('members'); // 'members', 'chat', 'files'
  const chatEndRef = useRef(null);
  const [groupFiles, setGroupFiles] = useState([]);
  const [myUploads, setMyUploads] = useState([]);
  const [shareFileId, setShareFileId] = useState('');

  useEffect(() => {
    fetchMyGroups();
    fetchAllGroups();
    fetchMyInvites();
  }, [location.key]);

  const fetchMyGroups = async () => {
    try {
      const res = await api.get('/share/groups');
      setMyGroups(res.data);
    } catch (err) { console.error('fetchMyGroups', err); }
  };

  const fetchAllGroups = async () => {
    try {
      const res = await api.get('/share/groups/all');
      setAllGroups(res.data);
    } catch (err) { console.error('fetchAllGroups', err); }
  };

  const fetchMyInvites = async () => {
    try {
      const res = await api.get('/share/groups/invites/mine');
      setMyInvites(res.data);
    } catch {}
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      await api.post('/share/groups', {
        name: newName.trim(),
        description: newDesc.trim() || null,
        join_mode: newJoinMode,
      });
      setNewName('');
      setNewDesc('');
      setNewJoinMode('open');
      setShowCreate(false);
      await fetchMyGroups();
      await fetchAllGroups();
    } catch {}
  };

  const handleJoin = async (group) => {
    try {
      const res = await api.post(`/share/groups/${group.id}/join`);
      setMsg(res.data.detail);
      setTimeout(() => setMsg(''), 3000);
      await fetchMyGroups();
      await fetchAllGroups();
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Failed');
      setTimeout(() => setMsg(''), 3000);
    }
  };

  const handleLeave = async (groupId) => {
    try {
      await api.post(`/share/groups/${groupId}/leave`);
      await fetchMyGroups();
      await fetchAllGroups();
      if (selectedGroup?.id === groupId) setSelectedGroup(null);
    } catch {}
  };

  const handleDelete = async (groupId) => {
    if (!confirm('Delete this group?')) return;
    try {
      await api.delete(`/share/groups/${groupId}`);
      await fetchMyGroups();
      await fetchAllGroups();
      if (selectedGroup?.id === groupId) setSelectedGroup(null);
    } catch {}
  };

  const viewMembers = async (group) => {
    setSelectedGroup(group);
    setGroupPanel('members');
    try {
      const res = await api.get(`/share/groups/${group.id}/members`);
      setMembers(res.data);
    } catch {}
    try {
      const res = await api.get(`/share/groups/${group.id}/join-requests`);
      setJoinRequests(res.data);
    } catch {
      setJoinRequests([]);
    }
  };

  const handleApprove = async (groupId, requestId) => {
    try {
      await api.post(`/share/groups/${groupId}/join-requests/${requestId}/approve`);
      await viewMembers(selectedGroup);
    } catch {}
  };

  const handleReject = async (groupId, requestId) => {
    try {
      await api.post(`/share/groups/${groupId}/join-requests/${requestId}/reject`);
      await viewMembers(selectedGroup);
    } catch {}
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteInput.trim() || !selectedGroup) return;
    try {
      const res = await api.post(`/share/groups/${selectedGroup.id}/invite`, {
        username_or_email: inviteInput.trim(),
      });
      setMsg(`Invited ${res.data.invitee_name}`);
      setInviteInput('');
      setTimeout(() => setMsg(''), 3000);
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Invite failed');
      setTimeout(() => setMsg(''), 3000);
    }
  };

  const handleAcceptInvite = async (inviteId) => {
    try {
      await api.post(`/share/groups/invites/${inviteId}/accept`);
      await fetchMyInvites();
      await fetchMyGroups();
      await fetchAllGroups();
    } catch {}
  };

  const handleDeclineInvite = async (inviteId) => {
    try {
      await api.post(`/share/groups/invites/${inviteId}/decline`);
      await fetchMyInvites();
    } catch {}
  };

  const fetchMessages = async (groupId) => {
    try {
      const res = await api.get(`/share/groups/${groupId}/messages`);
      setChatMessages(res.data);
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch {}
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || !selectedGroup) return;
    try {
      await api.post(`/share/groups/${selectedGroup.id}/messages`, { content: chatInput.trim() });
      setChatInput('');
      await fetchMessages(selectedGroup.id);
    } catch {}
  };

  const openChat = (group) => {
    setSelectedGroup(group);
    setGroupPanel('chat');
    fetchMessages(group.id);
  };

  const fetchGroupFiles = async (groupId) => {
    try {
      const res = await api.get(`/share/groups/${groupId}/files`);
      setGroupFiles(res.data);
    } catch {}
  };

  const fetchMyUploads = async () => {
    try {
      const res = await api.get('/uploads/');
      setMyUploads(res.data);
    } catch {}
  };

  const openFiles = (group) => {
    setSelectedGroup(group);
    setGroupPanel('files');
    fetchGroupFiles(group.id);
    fetchMyUploads();
  };

  const handleShareFile = async (e) => {
    e.preventDefault();
    if (!shareFileId || !selectedGroup) return;
    try {
      await api.post(`/share/groups/${selectedGroup.id}/files`, { upload_id: parseInt(shareFileId) });
      setShareFileId('');
      setMsg('File shared to group');
      setTimeout(() => setMsg(''), 3000);
      await fetchGroupFiles(selectedGroup.id);
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Share failed');
      setTimeout(() => setMsg(''), 3000);
    }
  };

  const handleRemoveFile = async (shareId) => {
    if (!selectedGroup) return;
    try {
      await api.delete(`/share/groups/${selectedGroup.id}/files/${shareId}`);
      await fetchGroupFiles(selectedGroup.id);
    } catch {}
  };

  const handleToggleJoinMode = async (group) => {
    const newMode = group.join_mode === 'approval' ? 'open' : 'approval';
    try {
      await api.patch(`/share/groups/${group.id}`, { join_mode: newMode });
      await fetchMyGroups();
      await fetchAllGroups();
      setMsg(newMode === 'approval' ? 'Join mode: Approval Required' : 'Join mode: Open');
      setTimeout(() => setMsg(''), 3000);
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Update failed');
      setTimeout(() => setMsg(''), 3000);
    }
  };

  const tabCls = (t) =>
    `px-4 py-2 text-sm font-medium rounded-lg transition ${
      tab === t
        ? 'bg-blue-600 text-white'
        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
    }`;

  const myGroupIds = new Set(myGroups.map((g) => g.id));

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Study Groups</h1>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition"
          >
            {showCreate ? 'Cancel' : '+ Create Group'}
          </button>
        </div>

        {msg && (
          <div className="mb-4 px-4 py-2 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg text-sm">
            {msg}
          </div>
        )}

        {showCreate && (
          <form onSubmit={handleCreate} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 mb-6 space-y-3">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Group name"
              className="w-full text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            />
            <textarea
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="Description (optional)"
              rows={2}
              className="w-full text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            />
            <div>
              <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">Join Mode</label>
              <select
                value={newJoinMode}
                onChange={(e) => setNewJoinMode(e.target.value)}
                className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="open">Open (anyone can join)</option>
                <option value="approval">Approval Required</option>
              </select>
            </div>
            <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700 transition">
              Create
            </button>
          </form>
        )}

        <div className="flex gap-2 mb-6">
          <button className={tabCls('my')} onClick={() => setTab('my')}>My Groups ({myGroups.length})</button>
          <button className={tabCls('all')} onClick={() => setTab('all')}>All Groups ({allGroups.length})</button>
          <button className={tabCls('invites')} onClick={() => { setTab('invites'); fetchMyInvites(); }}>
            Invites ({myInvites.length})
          </button>
        </div>

        {tab === 'invites' ? (
          <div className="space-y-3">
            {myInvites.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400">No pending invites.</p>
            )}
            {myInvites.map((inv) => (
              <div key={inv.id} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-900 dark:text-gray-100">
                    <span className="font-medium">{inv.inviter_name}</span> invited you to join{' '}
                    <span className="font-medium">{inv.group_name}</span>
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAcceptInvite(inv.id)}
                    className="text-xs bg-green-600 text-white px-3 py-1 rounded-lg hover:bg-green-700 transition"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => handleDeclineInvite(inv.id)}
                    className="text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
                  >
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(tab === 'my' ? myGroups : allGroups).map((g) => (
              <div key={g.id} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">{g.name}</h3>
                      {g.owner_id === user?.id ? (
                        <button
                          onClick={() => handleToggleJoinMode(g)}
                          title="Click to toggle join mode"
                          className={`text-xs px-2 py-0.5 rounded-full cursor-pointer transition ${
                            g.join_mode === 'approval'
                              ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-800'
                              : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800'
                          }`}
                        >
                          {g.join_mode === 'approval' ? 'Approval' : 'Open'}
                        </button>
                      ) : (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          g.join_mode === 'approval'
                            ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                            : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                        }`}>
                          {g.join_mode === 'approval' ? 'Approval' : 'Open'}
                        </span>
                      )}
                    </div>
                    {g.description && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{g.description}</p>}
                    <div className="flex gap-3 text-xs text-gray-400 dark:text-gray-500 mt-2">
                      <span>Owner: {g.owner_name}</span>
                      <span>{g.member_count} members</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => viewMembers(g)}
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Members
                  </button>
                  {myGroupIds.has(g.id) && (
                    <button
                      onClick={() => openChat(g)}
                      className="text-xs text-purple-600 dark:text-purple-400 hover:underline"
                    >
                      Chat
                    </button>
                  )}
                  {myGroupIds.has(g.id) && (
                    <button
                      onClick={() => openFiles(g)}
                      className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      Files
                    </button>
                  )}
                  {!myGroupIds.has(g.id) && (
                    <button onClick={() => handleJoin(g)} className="text-xs text-green-600 dark:text-green-400 hover:underline">
                      {g.join_mode === 'approval' ? 'Request to Join' : 'Join'}
                    </button>
                  )}
                  {myGroupIds.has(g.id) && g.owner_id !== user?.id && (
                    <button onClick={() => handleLeave(g.id)} className="text-xs text-yellow-600 dark:text-yellow-400 hover:underline">
                      Leave
                    </button>
                  )}
                  {myGroupIds.has(g.id) && g.owner_id === user?.id && (
                    <button onClick={() => handleDelete(g.id)} className="text-xs text-red-500 hover:underline">
                      Delete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedGroup && (
          <div className="mt-6 bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                  {selectedGroup.name}
                </h3>
                <div className="flex gap-1">
                  <button
                    onClick={() => { setGroupPanel('members'); viewMembers(selectedGroup); }}
                    className={`text-xs px-3 py-1 rounded-lg transition ${
                      groupPanel === 'members' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >
                    Members
                  </button>
                  {myGroupIds.has(selectedGroup.id) && (
                    <button
                      onClick={() => { setGroupPanel('chat'); fetchMessages(selectedGroup.id); }}
                      className={`text-xs px-3 py-1 rounded-lg transition ${
                        groupPanel === 'chat' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                    >
                      Chat
                    </button>
                  )}
                  {myGroupIds.has(selectedGroup.id) && (
                    <button
                      onClick={() => { setGroupPanel('files'); fetchGroupFiles(selectedGroup.id); fetchMyUploads(); }}
                      className={`text-xs px-3 py-1 rounded-lg transition ${
                        groupPanel === 'files' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                    >
                      Files
                    </button>
                  )}
                </div>
              </div>
              <button onClick={() => setSelectedGroup(null)} className="text-xs text-gray-400 hover:text-gray-600">
                Close
              </button>
            </div>

            {groupPanel === 'members' ? (
              <>
                <div className="space-y-2 mb-4">
                  {members.map((m) => (
                    <div key={m.id} className="flex items-center justify-between text-sm">
                      <span className="text-gray-700 dark:text-gray-300">{m.username}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        m.role === 'owner'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                      }`}>
                        {m.role}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Invite form */}
                {myGroupIds.has(selectedGroup.id) && (
                  <form onSubmit={handleInvite} className="flex gap-2 mb-4">
                    <input
                      type="text"
                      value={inviteInput}
                      onChange={(e) => setInviteInput(e.target.value)}
                      placeholder="Invite by username or email"
                      className="flex-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    />
                    <button type="submit" className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">
                      Invite
                    </button>
                  </form>
                )}

                {/* Join requests (owner only) */}
                {joinRequests.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Pending Join Requests
                    </h4>
                    <div className="space-y-2">
                      {joinRequests.map((r) => (
                        <div key={r.id} className="flex items-center justify-between text-sm bg-yellow-50 dark:bg-yellow-900/20 rounded-lg px-3 py-2">
                          <span className="text-gray-700 dark:text-gray-300">{r.username}</span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleApprove(selectedGroup.id, r.id)}
                              className="text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 transition"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReject(selectedGroup.id, r.id)}
                              className="text-xs bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 transition"
                            >
                              Reject
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : groupPanel === 'chat' ? (
              <div>
                {/* Chat messages */}
                <div className="h-80 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg p-3 mb-3 space-y-3">
                  {chatMessages.length === 0 && (
                    <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No messages yet. Start the conversation!</p>
                  )}
                  {chatMessages.map((m) => (
                    <div key={m.id} className="text-sm">
                      <div className="flex items-baseline gap-2">
                        <span className="font-medium text-gray-900 dark:text-gray-100">{m.username}</span>
                        <span className="text-xs text-gray-400 dark:text-gray-500">
                          {new Date(m.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-gray-700 dark:text-gray-300 mt-0.5">{m.content}</p>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>

                {/* Chat input */}
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  />
                  <button type="submit" className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">
                    Send
                  </button>
                </form>
              </div>
            ) : (
              <div>
                {/* Share file form */}
                <form onSubmit={handleShareFile} className="flex gap-2 mb-4">
                  <select
                    value={shareFileId}
                    onChange={(e) => setShareFileId(e.target.value)}
                    className="flex-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  >
                    <option value="">Select a file to share...</option>
                    {myUploads.map((u) => (
                      <option key={u.id} value={u.id}>{u.filename} ({u.file_type})</option>
                    ))}
                  </select>
                  <button type="submit" className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">
                    Share
                  </button>
                </form>

                {/* Shared files list */}
                <div className="space-y-2">
                  {groupFiles.length === 0 && (
                    <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-4">No files shared yet.</p>
                  )}
                  {groupFiles.map((f) => (
                    <div key={f.id} className="flex items-center justify-between text-sm bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2">
                      <div>
                        <span className="text-gray-900 dark:text-gray-100 font-medium">{f.filename}</span>
                        <span className="ml-2 text-xs text-gray-400">{f.file_type}</span>
                        <span className="ml-2 text-xs text-gray-400">by {f.owner_name}</span>
                      </div>
                      <button
                        onClick={() => handleRemoveFile(f.id)}
                        className="text-xs text-red-500 hover:underline"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}