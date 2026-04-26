import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import Navbar from '../components/Navbar';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import getApiErrorMessage from '../services/errorMessage';


export default function StudyGroupPage() {
  const { user } = useAuth();
  const [myGroups, setMyGroups] = useState([]);
  const [allGroups, setAllGroups] = useState([]);
  const [invites, setInvites] = useState([]);
  const [members, setMembers] = useState([]);
  const [groupMessages, setGroupMessages] = useState([]);
  const [groupFiles, setGroupFiles] = useState([]);
  const [joinRequests, setJoinRequests] = useState([]);
  const [myUploads, setMyUploads] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [joinMode, setJoinMode] = useState('open');
  const [groupMessage, setGroupMessage] = useState('');
  const [selectedUploadId, setSelectedUploadId] = useState('');
  const [inviteQuery, setInviteQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const myGroupIds = useMemo(() => new Set(myGroups.map((group) => group.id)), [myGroups]);
  const discoverGroups = useMemo(
    () => allGroups.filter((group) => !myGroupIds.has(group.id)),
    [allGroups, myGroupIds]
  );

  const selectedIsOwner = selectedGroup && user?.id === selectedGroup.owner_id;

  const loadPage = async () => {
    setError('');
    try {
      const [myGroupsRes, allGroupsRes, invitesRes, uploadsRes] = await Promise.all([
        api.get('/share/groups'),
        api.get('/share/groups/all'),
        api.get('/share/groups/invites/mine'),
        api.get('/uploads/', { params: { status: 'Completed' } }),
      ]);
      const myGroupsData = myGroupsRes.data || [];
      setMyGroups(myGroupsData);
      setAllGroups(allGroupsRes.data || []);
      setInvites(invitesRes.data || []);
      setMyUploads(uploadsRes.data || []);

      if (selectedGroup) {
        const refreshed = myGroupsData.find((group) => group.id === selectedGroup.id);
        if (refreshed) {
          await loadWorkspace(refreshed, false);
        } else {
          setSelectedGroup(null);
          setMembers([]);
          setGroupMessages([]);
          setGroupFiles([]);
          setJoinRequests([]);
        }
      }
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load study groups'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPage();
  }, []);

  const loadWorkspace = async (group, replaceSelection = true) => {
    setWorkspaceLoading(true);
    setError('');
    try {
      const requests = [
        api.get(`/share/groups/${group.id}/members`),
        api.get(`/share/groups/${group.id}/messages`),
        api.get(`/share/groups/${group.id}/files`),
      ];
      if (user?.id === group.owner_id) {
        requests.push(api.get(`/share/groups/${group.id}/join-requests`));
      }
      const responses = await Promise.all(requests);
      if (replaceSelection) {
        setSelectedGroup(group);
      }
      setMembers(responses[0].data || []);
      setGroupMessages(responses[1].data || []);
      setGroupFiles(responses[2].data || []);
      setJoinRequests(user?.id === group.owner_id ? (responses[3]?.data || []) : []);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load group workspace'));
      setMembers([]);
      setGroupMessages([]);
      setGroupFiles([]);
      setJoinRequests([]);
    } finally {
      setWorkspaceLoading(false);
    }
  };

  const createGroup = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      const res = await api.post('/share/groups', {
        name: name.trim(),
        description: description.trim() || null,
        join_mode: joinMode,
      });
      setName('');
      setDescription('');
      setJoinMode('open');
      setMessage('Study group created.');
      await loadPage();
      await loadWorkspace(res.data);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to create study group'));
    }
  };

  const joinGroup = async (groupId) => {
    setError('');
    setMessage('');
    try {
      const res = await api.post(`/share/groups/${groupId}/join`);
      setMessage(res.data?.detail || 'Joined group.');
      await loadPage();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to join group'));
    }
  };

  const leaveGroup = async (groupId) => {
    setError('');
    setMessage('');
    try {
      const res = await api.post(`/share/groups/${groupId}/leave`);
      setMessage(res.data?.detail || 'Left group.');
      if (selectedGroup?.id === groupId) {
        setSelectedGroup(null);
        setMembers([]);
        setGroupMessages([]);
        setGroupFiles([]);
        setJoinRequests([]);
      }
      await loadPage();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to leave group'));
    }
  };

  const respondInvite = async (inviteId, action) => {
    setError('');
    setMessage('');
    try {
      const res = await api.post(`/share/groups/invites/${inviteId}/${action}`);
      setMessage(res.data?.detail || 'Invite updated.');
      await loadPage();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to update invite'));
    }
  };

  const sendGroupMessage = async (e) => {
    e.preventDefault();
    if (!selectedGroup || !groupMessage.trim()) return;

    setError('');
    try {
      const res = await api.post(`/share/groups/${selectedGroup.id}/messages`, {
        content: groupMessage.trim(),
      });
      setGroupMessages((prev) => [...prev, res.data]);
      setGroupMessage('');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to send message'));
    }
  };

  const shareFileToGroup = async () => {
    if (!selectedGroup || !selectedUploadId) return;

    setError('');
    setMessage('');
    try {
      const res = await api.post(`/share/groups/${selectedGroup.id}/files`, {
        upload_id: parseInt(selectedUploadId, 10),
      });
      setGroupFiles((prev) => [res.data, ...prev]);
      setSelectedUploadId('');
      setMessage('File shared to group.');
      await api.post(`/share/groups/${selectedGroup.id}/messages`, {
        content: `Shared file: ${res.data.filename}`,
      });
      await loadWorkspace(selectedGroup, false);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to share file'));
    }
  };

  const removeGroupFile = async (shareId) => {
    if (!selectedGroup) return;

    setError('');
    try {
      await api.delete(`/share/groups/${selectedGroup.id}/files/${shareId}`);
      setGroupFiles((prev) => prev.filter((file) => file.id !== shareId));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to remove file'));
    }
  };

  const inviteToGroup = async (e) => {
    e.preventDefault();
    if (!selectedGroup || !inviteQuery.trim()) return;

    setError('');
    setMessage('');
    try {
      const res = await api.post(`/share/groups/${selectedGroup.id}/invite`, {
        username_or_email: inviteQuery.trim(),
      });
      setInviteQuery('');
      setMessage(`Invited ${res.data.invitee_name || 'user'} to the group.`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to send invite'));
    }
  };

  const respondJoinRequest = async (requestId, action) => {
    if (!selectedGroup) return;

    setError('');
    try {
      const res = await api.post(`/share/groups/${selectedGroup.id}/join-requests/${requestId}/${action}`);
      setMessage(res.data?.detail || 'Join request updated.');
      await loadWorkspace(selectedGroup, false);
      await loadPage();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to update join request'));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Study Groups</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Create groups, chat with members, and share uploaded materials.</p>
          </div>
          <button
            onClick={loadPage}
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

        {message && (
          <div className="bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 p-3 rounded-lg mb-6 text-sm">
            {message}
          </div>
        )}

        <div className="grid lg:grid-cols-[380px_minmax(0,1fr)] gap-6">
          <section className="space-y-6">
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">Create a Group</h2>
              <form onSubmit={createGroup} className="space-y-3">
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Group name"
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  required
                />
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Description"
                  rows={3}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                />
                <div className="flex flex-wrap gap-3 items-center">
                  <select
                    value={joinMode}
                    onChange={(e) => setJoinMode(e.target.value)}
                    className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  >
                    <option value="open">Open join</option>
                    <option value="approval">Approval required</option>
                  </select>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition"
                  >
                    Create Group
                  </button>
                </div>
              </form>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">My Groups</h2>
              {loading ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">Loading groups...</p>
              ) : myGroups.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">You have not joined any groups yet.</p>
              ) : (
                <div className="space-y-3">
                  {myGroups.map((group) => {
                    const isOwner = user?.id === group.owner_id;
                    const isSelected = selectedGroup?.id === group.id;
                    return (
                      <div key={group.id} className={`border rounded-lg p-4 ${isSelected ? 'border-blue-500 dark:border-blue-500' : 'border-gray-200 dark:border-gray-700'}`}>
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{group.name}</h3>
                          <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                            {group.join_mode === 'approval' ? 'Approval' : 'Open'}
                          </span>
                          {isOwner && (
                            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">
                              Owner
                            </span>
                          )}
                        </div>
                        {group.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{group.description}</p>
                        )}
                        <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                          <span>{group.member_count} members</span>
                          <span>Owner: {group.owner_name || 'Unknown'}</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => loadWorkspace(group)}
                            className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                          >
                            Open Workspace
                          </button>
                          {!isOwner && (
                            <button
                              onClick={() => leaveGroup(group.id)}
                              className="px-3 py-1.5 rounded-lg border border-red-300 dark:border-red-700 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
                            >
                              Leave
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">Pending Invites</h2>
              {invites.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">No pending invites.</p>
              ) : (
                <div className="space-y-3">
                  {invites.map((invite) => (
                    <div key={invite.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">{invite.group_name}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">Invited by {invite.inviter_name || 'Unknown'}</p>
                      <div className="flex gap-2 mt-3">
                        <button
                          onClick={() => respondInvite(invite.id, 'accept')}
                          className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition"
                        >
                          Accept
                        </button>
                        <button
                          onClick={() => respondInvite(invite.id, 'decline')}
                          className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                        >
                          Decline
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">Discover Groups</h2>
              {loading ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">Loading groups...</p>
              ) : discoverGroups.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">No other groups available right now.</p>
              ) : (
                <div className="space-y-3">
                  {discoverGroups.map((group) => (
                    <div key={group.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{group.name}</h3>
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                          {group.join_mode === 'approval' ? 'Approval' : 'Open'}
                        </span>
                      </div>
                      {group.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{group.description}</p>
                      )}
                      <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                        <span>{group.member_count} members</span>
                        <span>Owner: {group.owner_name || 'Unknown'}</span>
                      </div>
                      <button
                        onClick={() => joinGroup(group.id)}
                        className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition"
                      >
                        {group.join_mode === 'approval' ? 'Request to Join' : 'Join Group'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="space-y-6">
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-5">
              <div className="flex items-center justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                    {selectedGroup ? selectedGroup.name : 'Group Workspace'}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {selectedGroup ? (selectedGroup.description || 'Chat, members, and shared files for this group.') : 'Select one of your groups to open its workspace.'}
                  </p>
                </div>
                {selectedGroup && (
                  <button
                    onClick={() => loadWorkspace(selectedGroup, false)}
                    className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                  >
                    Refresh Workspace
                  </button>
                )}
              </div>

              {!selectedGroup ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">Pick a group from the left column.</p>
              ) : workspaceLoading ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">Loading workspace...</p>
              ) : (
                <div className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Members</h3>
                      {members.length === 0 ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400">No members found.</p>
                      ) : (
                        <div className="space-y-2">
                          {members.map((member) => (
                            <div key={member.id} className="flex items-center justify-between text-sm">
                              <span className="text-gray-900 dark:text-gray-100">{member.username || `User #${member.user_id}`}</span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">{member.role}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Shared Files</h3>
                      <div className="flex flex-wrap gap-2 mb-3">
                        <select
                          value={selectedUploadId}
                          onChange={(e) => setSelectedUploadId(e.target.value)}
                          className="flex-1 min-w-[180px] border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                        >
                          <option value="">Select one of your completed uploads</option>
                          {myUploads.map((upload) => (
                            <option key={upload.id} value={upload.id}>{upload.filename}</option>
                          ))}
                        </select>
                        <button
                          onClick={shareFileToGroup}
                          disabled={!selectedUploadId}
                          className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
                        >
                          Share File
                        </button>
                      </div>
                      {groupFiles.length === 0 ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400">No files shared to this group yet.</p>
                      ) : (
                        <div className="space-y-2">
                          {groupFiles.map((file) => (
                            <div key={file.id} className="border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2">
                              <div className="flex items-center justify-between gap-3">
                                <div className="min-w-0">
                                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{file.filename}</p>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">
                                    {String(file.file_type || '').toUpperCase()} · Shared by {file.owner_name || 'Unknown'} · {file.permission || 'read'}
                                  </p>
                                </div>
                                <div className="flex items-center gap-3 shrink-0">
                                  <Link
                                    to={`/uploads/${file.upload_id}`}
                                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                  >
                                    Open Analysis
                                  </Link>
                                  {(user?.id === file.shared_by || selectedIsOwner) && (
                                    <button
                                      onClick={() => removeGroupFile(file.id)}
                                      className="text-xs text-red-600 dark:text-red-400 hover:underline"
                                    >
                                      Remove
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Group Chat</h3>
                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-gray-50 dark:bg-gray-950/40 h-[320px] overflow-y-auto space-y-3">
                      {groupMessages.length === 0 ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400">No messages yet.</p>
                      ) : (
                        groupMessages.map((entry) => (
                          <div key={entry.id} className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2">
                            <div className="flex items-center justify-between gap-3 mb-1">
                              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{entry.username || `User #${entry.user_id}`}</span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">{new Date(entry.created_at).toLocaleString()}</span>
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{entry.content}</p>
                          </div>
                        ))
                      )}
                    </div>
                    <form onSubmit={sendGroupMessage} className="flex gap-2 mt-3">
                      <input
                        type="text"
                        value={groupMessage}
                        onChange={(e) => setGroupMessage(e.target.value)}
                        placeholder="Send a message to the group"
                        className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                      />
                      <button
                        type="submit"
                        disabled={!groupMessage.trim()}
                        className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
                      >
                        Send
                      </button>
                    </form>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Invite Member</h3>
                      <form onSubmit={inviteToGroup} className="flex gap-2">
                        <input
                          type="text"
                          value={inviteQuery}
                          onChange={(e) => setInviteQuery(e.target.value)}
                          placeholder="Username or email"
                          className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                        />
                        <button
                          type="submit"
                          disabled={!inviteQuery.trim()}
                          className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 transition"
                        >
                          Invite
                        </button>
                      </form>
                    </div>

                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Join Requests</h3>
                      {!selectedIsOwner ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400">Only the group owner can review join requests.</p>
                      ) : joinRequests.length === 0 ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400">No pending join requests.</p>
                      ) : (
                        <div className="space-y-3">
                          {joinRequests.map((request) => (
                            <div key={request.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{request.username || `User #${request.user_id}`}</p>
                              <div className="flex gap-2 mt-3">
                                <button
                                  onClick={() => respondJoinRequest(request.id, 'approve')}
                                  className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition"
                                >
                                  Approve
                                </button>
                                <button
                                  onClick={() => respondJoinRequest(request.id, 'reject')}
                                  className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                                >
                                  Reject
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
