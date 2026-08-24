import { useEffect, useMemo, useState } from 'react';
import { getAllTracks } from '../api/tracks.js';
import {
  addTrackToPlaylist,
  createPlaylist,
  deletePlaylist,
  getAllPlaylists,
  removeTrackFromPlaylist,
} from '../api/playlists.js';

const EMPTY_PLAYLIST = {
  name: '',
  description: '',
  cover_url: '',
};

export default function Playlists({ onPlayTrack }) {
  const [playlists, setPlaylists] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_PLAYLIST);
  const [saving, setSaving] = useState(false);
  const [trackToAdd, setTrackToAdd] = useState('');

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [playlistData, trackData] = await Promise.all([
        getAllPlaylists({ limit: 200 }),
        getAllTracks({ limit: 200 }),
      ]);
      setPlaylists(playlistData || []);
      setTracks(trackData || []);
    } catch (err) {
      setError(err?.message || 'Failed to load playlists');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const selected = useMemo(
    () => playlists.find((playlist) => playlist.id === selectedId) || null,
    [playlists, selectedId]
  );

  const selectedTracks = useMemo(() => {
    if (!selected) return [];
    const ids = selected.track_ids || [];
    const byId = new Map(tracks.map((track) => [track.id, track]));
    return ids.map((id) => byId.get(id)).filter(Boolean);
  }, [selected, tracks]);

  const availableTracks = useMemo(() => {
    const used = new Set(selected?.track_ids || []);
    return tracks.filter((track) => !used.has(track.id));
  }, [tracks, selected]);

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createPlaylist({
        ...form,
        track_ids: [],
      });
      setCreateOpen(false);
      setForm(EMPTY_PLAYLIST);
      await loadData();
      if (created?.id) setSelectedId(created.id);
    } catch (err) {
      setError(err?.message || 'Failed to create playlist');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(playlist) {
    if (!window.confirm(`Delete playlist “${playlist.name}”?`)) return;
    try {
      await deletePlaylist(playlist.id);
      if (selectedId === playlist.id) setSelectedId(null);
      setPlaylists((prev) => prev.filter((item) => item.id !== playlist.id));
    } catch (err) {
      setError(err?.message || 'Failed to delete playlist');
    }
  }

  async function handleAddTrack() {
    if (!selected || !trackToAdd) return;
    setError(null);
    try {
      const updated = await addTrackToPlaylist(selected.id, trackToAdd);
      setPlaylists((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item))
      );
      setTrackToAdd('');
    } catch (err) {
      setError(err?.message || 'Failed to add track');
    }
  }

  async function handleRemoveTrack(trackId) {
    if (!selected) return;
    setError(null);
    try {
      const updated = await removeTrackFromPlaylist(selected.id, trackId);
      setPlaylists((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item))
      );
    } catch (err) {
      setError(err?.message || 'Failed to remove track');
    }
  }

  if (loading) {
    return (
      <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/70 p-10 text-center text-[var(--color-muted)] animate-pulse-soft">
        Loading playlists…
      </div>
    );
  }

  if (selected) {
    return (
      <section className="animate-fade-up space-y-6">
        <button
          type="button"
          onClick={() => setSelectedId(null)}
          className="text-sm text-[var(--color-muted)] hover:text-[var(--color-accent)]"
        >
          ← Back to playlists
        </button>

        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div className="flex gap-4">
            {selected.cover_url ? (
              <img
                src={selected.cover_url}
                alt=""
                className="h-28 w-28 rounded-2xl object-cover"
              />
            ) : (
              <div className="flex h-28 w-28 items-center justify-center rounded-2xl bg-[var(--color-panel-2)] text-[var(--color-muted)]">
                Cover
              </div>
            )}
            <div>
              <h2 className="font-display text-3xl font-semibold">{selected.name}</h2>
              <p className="mt-1 max-w-xl text-sm text-[var(--color-muted)]">
                {selected.description || 'No description'}
              </p>
              <p className="mt-2 text-xs text-[var(--color-muted)]">
                {(selected.track_ids || []).length} tracks
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => handleDelete(selected)}
            className="rounded-xl border border-[var(--color-danger)]/40 px-4 py-2 text-sm text-[var(--color-danger)]"
          >
            Delete playlist
          </button>
        </div>

        {error && (
          <div className="rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-3 rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80 p-4 sm:flex-row">
          <select
            value={trackToAdd}
            onChange={(event) => setTrackToAdd(event.target.value)}
            className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-3 py-2.5 text-sm outline-none"
          >
            <option value="">Add a track…</option>
            {availableTracks.map((track) => (
              <option key={track.id} value={track.id}>
                {track.title} — {track.artist}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleAddTrack}
            disabled={!trackToAdd}
            className="rounded-xl bg-[var(--color-accent)] px-4 py-2.5 text-sm font-semibold text-ink disabled:opacity-50"
          >
            Add track
          </button>
        </div>

        <div className="overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80">
          {selectedTracks.length === 0 ? (
            <p className="px-4 py-10 text-center text-sm text-[var(--color-muted)]">
              This playlist is empty. Add tracks above.
            </p>
          ) : (
            <ul>
              {selectedTracks.map((track, index) => (
                <li
                  key={track.id}
                  className="flex items-center justify-between gap-3 border-b border-[var(--color-line)]/70 px-4 py-3 last:border-b-0"
                >
                  <button
                    type="button"
                    onClick={() => onPlayTrack?.(track)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <div className="truncate font-medium hover:text-[var(--color-accent)]">
                      {index + 1}. {track.title}
                    </div>
                    <div className="truncate text-sm text-[var(--color-muted)]">
                      {track.artist}
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRemoveTrack(track.id)}
                    className="text-xs text-[var(--color-danger)] hover:underline"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    );
  }

  return (
    <section className="animate-fade-up space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="font-display text-3xl font-semibold tracking-tight">Playlists</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Open a playlist to manage its tracks.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="rounded-xl bg-[var(--color-accent)] px-4 py-2.5 text-sm font-semibold text-ink transition hover:brightness-110"
        >
          Create playlist
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        {playlists.map((playlist) => (
          <button
            key={playlist.id}
            type="button"
            onClick={() => setSelectedId(playlist.id)}
            className="overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80 text-left transition hover:border-[var(--color-accent)]/60 hover:bg-[var(--color-panel-2)]"
          >
            {playlist.cover_url ? (
              <img
                src={playlist.cover_url}
                alt=""
                className="h-44 w-full object-cover"
              />
            ) : (
              <div className="flex h-44 w-full items-center justify-center bg-[var(--color-panel-2)] text-[var(--color-muted)]">
                No cover
              </div>
            )}
            <div className="space-y-1 p-4">
              <h3 className="font-semibold">{playlist.name}</h3>
              <p className="line-clamp-2 text-sm text-[var(--color-muted)]">
                {playlist.description || 'No description'}
              </p>
              <p className="text-xs text-[var(--color-muted)]">
                {(playlist.track_ids || []).length} tracks
              </p>
            </div>
          </button>
        ))}
      </div>

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <form
            onSubmit={handleCreate}
            className="w-full max-w-md space-y-4 rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)] p-6"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-display text-xl font-semibold">New playlist</h3>
              <button type="button" onClick={() => setCreateOpen(false)} className="text-[var(--color-muted)]">
                Close
              </button>
            </div>
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Name *</span>
              <input
                required
                value={form.name}
                onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-3 py-2 outline-none focus:border-[var(--color-accent)]"
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Description</span>
              <textarea
                value={form.description}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, description: event.target.value }))
                }
                rows={3}
                className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-3 py-2 outline-none focus:border-[var(--color-accent)]"
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Cover URL</span>
              <input
                value={form.cover_url}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, cover_url: event.target.value }))
                }
                className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-3 py-2 outline-none focus:border-[var(--color-accent)]"
              />
            </label>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setCreateOpen(false)}
                className="rounded-xl border border-[var(--color-line)] px-4 py-2 text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-[var(--color-accent)] px-4 py-2 text-sm font-semibold text-ink disabled:opacity-60"
              >
                {saving ? 'Creating…' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
