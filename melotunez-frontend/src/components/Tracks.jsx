import { useEffect, useMemo, useState } from 'react';
import {
  createTrack,
  deleteTrack,
  getAllTracks,
  updateTrack,
} from '../api/tracks.js';

const EMPTY_FORM = {
  title: '',
  artist: '',
  album: '',
  genre: '',
  duration: 0,
  cover_url: '',
  audio_url: '',
  plays: 0,
};

function formatDuration(seconds) {
  const total = Math.max(0, Number(seconds) || 0);
  const mins = Math.floor(total / 60);
  const secs = Math.floor(total % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default function Tracks({ onPlayTrack }) {
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  async function loadTracks(search = query) {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllTracks({ q: search, limit: 200 });
      setTracks(data || []);
    } catch (err) {
      setError(err?.message || 'Failed to load tracks');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTracks('');
  }, []);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return tracks;
    return tracks.filter(
      (track) =>
        String(track.title || '').toLowerCase().includes(term) ||
        String(track.artist || '').toLowerCase().includes(term)
    );
  }, [tracks, query]);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  }

  function openEdit(track) {
    setEditing(track);
    setForm({
      title: track.title || '',
      artist: track.artist || '',
      album: track.album || '',
      genre: track.genre || '',
      duration: track.duration || 0,
      cover_url: track.cover_url || '',
      audio_url: track.audio_url || '',
      plays: track.plays || 0,
    });
    setModalOpen(true);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const payload = {
      ...form,
      duration: Number(form.duration) || 0,
      plays: Number(form.plays) || 0,
    };
    try {
      if (editing) {
        await updateTrack(editing.id, payload);
      } else {
        await createTrack(payload);
      }
      setModalOpen(false);
      setEditing(null);
      setForm(EMPTY_FORM);
      await loadTracks(query);
    } catch (err) {
      setError(err?.message || 'Failed to save track');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(track) {
    if (!window.confirm(`Delete “${track.title}”?`)) return;
    setError(null);
    try {
      await deleteTrack(track.id);
      setTracks((prev) => prev.filter((item) => item.id !== track.id));
    } catch (err) {
      setError(err?.message || 'Failed to delete track');
    }
  }

  return (
    <section className="animate-fade-up space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="font-display text-3xl font-semibold tracking-tight">Tracks</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Browse, search, and manage the MeloTunez catalog.
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="rounded-xl bg-[var(--color-accent)] px-4 py-2.5 text-sm font-semibold text-ink transition hover:brightness-110"
        >
          Add Track
        </button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by title or artist…"
          className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] px-4 py-2.5 text-sm outline-none ring-[var(--color-accent)] placeholder:text-[var(--color-muted)] focus:ring-2"
        />
        <button
          type="button"
          onClick={() => loadTracks(query)}
          className="rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-4 py-2.5 text-sm font-medium hover:border-[var(--color-accent)]"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/70 p-10 text-center text-[var(--color-muted)] animate-pulse-soft">
          Loading tracks…
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-[var(--color-line)] text-[var(--color-muted)]">
              <tr>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Artist</th>
                <th className="px-4 py-3 font-medium">Album</th>
                <th className="px-4 py-3 font-medium">Genre</th>
                <th className="px-4 py-3 font-medium">Duration</th>
                <th className="px-4 py-3 font-medium">Plays</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-[var(--color-muted)]">
                    No tracks found.
                  </td>
                </tr>
              ) : (
                filtered.map((track) => (
                  <tr
                    key={track.id}
                    className="border-b border-[var(--color-line)]/70 transition hover:bg-white/5"
                  >
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => onPlayTrack?.(track)}
                        className="text-left font-medium hover:text-[var(--color-accent)]"
                      >
                        {track.title}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-muted)]">{track.artist}</td>
                    <td className="px-4 py-3 text-[var(--color-muted)]">{track.album || '—'}</td>
                    <td className="px-4 py-3 text-[var(--color-muted)]">{track.genre || '—'}</td>
                    <td className="px-4 py-3 tabular-nums text-[var(--color-muted)]">
                      {formatDuration(track.duration)}
                    </td>
                    <td className="px-4 py-3 tabular-nums text-[var(--color-muted)]">
                      {track.plays ?? 0}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => onPlayTrack?.(track)}
                          className="rounded-lg px-2.5 py-1 text-xs font-medium text-[var(--color-accent)] hover:bg-white/5"
                        >
                          Play
                        </button>
                        <button
                          type="button"
                          onClick={() => openEdit(track)}
                          className="rounded-lg px-2.5 py-1 text-xs font-medium text-[var(--color-cream)] hover:bg-white/5"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(track)}
                          className="rounded-lg px-2.5 py-1 text-xs font-medium text-[var(--color-danger)] hover:bg-white/5"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <form
            onSubmit={handleSubmit}
            className="w-full max-w-xl space-y-4 rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)] p-6 shadow-2xl"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-display text-xl font-semibold">
                {editing ? 'Edit Track' : 'Add Track'}
              </h3>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-[var(--color-muted)] hover:text-white"
              >
                Close
              </button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {[
                ['title', 'Title *', true],
                ['artist', 'Artist *', true],
                ['album', 'Album', false],
                ['genre', 'Genre', false],
                ['duration', 'Duration (sec)', false, 'number'],
                ['plays', 'Plays', false, 'number'],
                ['cover_url', 'Cover URL', false],
                ['audio_url', 'Audio URL *', true],
              ].map(([key, label, required, type = 'text']) => (
                <label key={key} className={`block space-y-1 text-sm ${key === 'audio_url' || key === 'cover_url' ? 'sm:col-span-2' : ''}`}>
                  <span className="text-[var(--color-muted)]">{label}</span>
                  <input
                    required={required}
                    type={type}
                    value={form[key]}
                    onChange={(event) =>
                      setForm((prev) => ({
                        ...prev,
                        [key]:
                          type === 'number'
                            ? Number(event.target.value)
                            : event.target.value,
                      }))
                    }
                    className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-3 py-2 outline-none focus:border-[var(--color-accent)]"
                  />
                </label>
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-xl border border-[var(--color-line)] px-4 py-2 text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-[var(--color-accent)] px-4 py-2 text-sm font-semibold text-ink disabled:opacity-60"
              >
                {saving ? 'Saving…' : editing ? 'Save changes' : 'Create track'}
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
