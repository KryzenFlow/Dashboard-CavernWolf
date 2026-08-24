/**
 * Option 3 reference App (user paste: "Truetunes" branding preserved).
 *
 * NOT wired into main.jsx — production UI is src/App.jsx + src/components/*
 * via the Express `/api` proxy. To experiment with this monolith, temporarily
 * import it from main.jsx and install Option 3 deps (see package.snippet.json).
 */
import { useState, useEffect } from 'react';
import { getAllTracks, createTrack, deleteTrack, updateTrack } from './api/tracks.js';
import { getAllPlaylists, createPlaylist, deletePlaylist, addTrackToPlaylist } from './api/playlists.js';
import { getAllUsers } from './api/users.js';

export default function App() {
  const [view, setView] = useState('tracks');
  const [tracks, setTracks] = useState([]);
  const [playlists, setPlaylists] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [showAddTrack, setShowAddTrack] = useState(false);
  const [newTrack, setNewTrack] = useState({
    title: '', artist: '', album: '', genre: '', duration: 0,
    cover_url: '', audio_url: '', plays: 0
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [trackData, playlistData, userData] = await Promise.all([
        getAllTracks(),
        getAllPlaylists(),
        getAllUsers()
      ]);
      setTracks(trackData || []);
      setPlaylists(playlistData || []);
      setUsers(userData || []);
    } catch (err) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTrack(e) {
    e.preventDefault();
    try {
      await createTrack(newTrack);
      setShowAddTrack(false);
      setNewTrack({ title: '', artist: '', album: '', genre: '', duration: 0, cover_url: '', audio_url: '', plays: 0 });
      const refreshed = await getAllTracks();
      setTracks(refreshed || []);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteTrack(id) {
    if (!confirm('Delete this track?')) return;
    try {
      await deleteTrack(id);
      setTracks(tracks.filter(t => t.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <div className="text-2xl">Loading Truetunes...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Sidebar */}
      <div className="w-64 bg-black p-6 flex flex-col gap-4">
        <h1 className="text-2xl font-bold text-green-500 mb-8">🎵 Truetunes</h1>
        <button
          onClick={() => setView('tracks')}
          className={`text-left px-4 py-2 rounded ${view === 'tracks' ? 'bg-green-500 text-black' : 'hover:bg-gray-800'}`}
        >
          🎶 Tracks
        </button>
        <button
          onClick={() => setView('playlists')}
          className={`text-left px-4 py-2 rounded ${view === 'playlists' ? 'bg-green-500 text-black' : 'hover:bg-gray-800'}`}
        >
          📋 Playlists
        </button>
        <button
          onClick={() => setView('users')}
          className={`text-left px-4 py-2 rounded ${view === 'users' ? 'bg-green-500 text-black' : 'hover:bg-gray-800'}`}
        >
          👥 Users
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-8">
        {error && (
          <div className="bg-red-600 text-white p-4 rounded mb-4">
            ⚠️ {error}
          </div>
        )}

        {/* TRACKS VIEW */}
        {view === 'tracks' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold">Tracks</h2>
              <button
                onClick={() => setShowAddTrack(true)}
                className="bg-green-500 text-black px-4 py-2 rounded font-bold hover:bg-green-400"
              >
                + Add Track
              </button>
            </div>

            {showAddTrack && (
              <form onSubmit={handleCreateTrack} className="bg-gray-800 p-6 rounded mb-6 grid grid-cols-2 gap-4">
                <input
                  placeholder="Title *" required
                  value={newTrack.title}
                  onChange={e => setNewTrack({...newTrack, title: e.target.value})}
                  className="p-2 bg-gray-700 rounded text-white"
                />
                <input
                  placeholder="Artist *" required
                  value={newTrack.artist}
                  onChange={e => setNewTrack({...newTrack, artist: e.target.value})}
                  className="p-2 bg-gray-700 rounded text-white"
                />
                <input
                  placeholder="Album"
                  value={newTrack.album}
                  onChange={e => setNewTrack({...newTrack, album: e.target.value})}
                  className="p-2 bg-gray-700 rounded text-white"
                />
                <input
                  placeholder="Genre"
                  value={newTrack.genre}
                  onChange={e => setNewTrack({...newTrack, genre: e.target.value})}
                  className="p-2 bg-gray-700 rounded text-white"
                />
                <input
                  type="number"
                  placeholder="Duration (sec)"
                  value={newTrack.duration}
                  onChange={e => setNewTrack({...newTrack, duration: Number(e.target.value)})}
                  className="p-2 bg-gray-700 rounded text-white"
                />
                <input
                  placeholder="Cover URL"
                  value={newTrack.cover_url}
                  onChange={e => setNewTrack({...newTrack, cover_url: e.target.value})}
                  className="p-2 bg-gray-700 rounded text-white"
                />
                <input
                  placeholder="Audio URL *" required
                  value={newTrack.audio_url}
                  onChange={e => setNewTrack({...newTrack, audio_url: e.target.value})}
                  className="p-2 bg-gray-700 rounded text-white col-span-2"
                />
                <div className="col-span-2 flex gap-4">
                  <button type="submit" className="bg-green-500 text-black px-6 py-2 rounded font-bold">Create</button>
                  <button type="button" onClick={() => setShowAddTrack(false)} className="bg-gray-600 px-6 py-2 rounded">Cancel</button>
                </div>
              </form>
            )}

            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-gray-700 text-gray-400">
                  <th className="py-3">Cover</th>
                  <th>Title</th>
                  <th>Artist</th>
                  <th>Album</th>
                  <th>Genre</th>
                  <th>Duration</th>
                  <th>Plays</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tracks.map(track => (
                  <tr key={track.id} className="border-b border-gray-800 hover:bg-gray-800">
                    <td className="py-2">
                      {track.cover_url ? (
                        <img src={track.cover_url} alt="" className="w-12 h-12 rounded" />
                      ) : (
                        <div className="w-12 h-12 bg-gray-700 rounded flex items-center justify-center">🎵</div>
                      )}
                    </td>
                    <td className="cursor-pointer hover:text-green-500" onClick={() => setCurrentTrack(track)}>
                      {track.title}
                    </td>
                    <td>{track.artist}</td>
                    <td>{track.album || '-'}</td>
                    <td>{track.genre || '-'}</td>
                    <td>{formatDuration(track.duration || 0)}</td>
                    <td>{track.plays || 0}</td>
                    <td>
                      <button
                        onClick={() => handleDeleteTrack(track.id)}
                        className="text-red-500 hover:text-red-400 text-sm"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* PLAYLISTS VIEW */}
        {view === 'playlists' && (
          <div>
            <h2 className="text-3xl font-bold mb-6">Playlists</h2>
            <div className="grid grid-cols-4 gap-6">
              {playlists.map(playlist => (
                <div
                  key={playlist.id}
                  className="bg-gray-800 rounded-lg p-4 cursor-pointer hover:bg-gray-700 transition"
                >
                  {playlist.cover_url ? (
                    <img src={playlist.cover_url} alt="" className="w-full h-40 rounded mb-3 object-cover" />
                  ) : (
                    <div className="w-full h-40 bg-gray-700 rounded mb-3 flex items-center justify-center text-4xl">📋</div>
                  )}
                  <h3 className="font-bold">{playlist.name}</h3>
                  <p className="text-gray-400 text-sm">{playlist.description || 'No description'}</p>
                  <p className="text-gray-500 text-xs mt-1">{playlist.track_ids?.length || 0} tracks</p>
                  <button
                    onClick={async () => {
                      if (confirm('Delete this playlist?')) {
                        await deletePlaylist(playlist.id);
                        setPlaylists(playlists.filter(p => p.id !== playlist.id));
                      }
                    }}
                    className="text-red-500 text-sm mt-2"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* USERS VIEW */}
        {view === 'users' && (
          <div>
            <h2 className="text-3xl font-bold mb-6">Users</h2>
            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-gray-700 text-gray-400">
                  <th className="py-3">Name</th>
                  <th>Email</th>
                  <th>Role</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id} className="border-b border-gray-800">
                    <td className="py-3">{user.full_name}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className={`px-2 py-1 rounded text-xs ${user.role === 'admin' ? 'bg-green-500 text-black' : 'bg-gray-700'}`}>
                        {user.role}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audio Player Bar */}
      {currentTrack && (
        <div className="fixed bottom-0 left-64 right-0 bg-black p-4 flex items-center gap-4 border-t border-gray-700">
          <img
            src={currentTrack.cover_url || ''}
            alt=""
            className="w-12 h-12 rounded"
            onError={(e) => e.target.style.display = 'none'}
          />
          <div>
            <div className="font-bold">{currentTrack.title}</div>
            <div className="text-gray-400 text-sm">{currentTrack.artist}</div>
          </div>
          <audio
            src={currentTrack.audio_url}
            controls
            autoPlay
            className="flex-1"
          />
          <button
            onClick={() => setCurrentTrack(null)}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}