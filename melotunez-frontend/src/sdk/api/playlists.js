/**
 * Option 3 — Playlist helpers via Base44 SDK (browser).
 *
 * App components should keep using `src/api/playlists.js` (Express proxy).
 * SDK `list` signature is list(sort, limit, skip, fields) — not an options object.
 * Exported API keeps the user's options-object shape; `q` is applied client-side.
 */
import { base44 } from '../lib/base44.js';

function matchesQuery(playlist, q) {
  if (!q) return true;
  const term = String(q).toLowerCase().trim();
  if (!term) return true;
  return ['name', 'description'].some((field) =>
    String(playlist?.[field] ?? '')
      .toLowerCase()
      .includes(term),
  );
}

export async function getAllPlaylists(options = {}) {
  const { q, limit = 50, skip = 0, sort_by } = options;
  const sort = sort_by || '-created_date';
  const records = await base44.entities.Playlist.list(sort, limit, skip);
  return (records || []).filter((playlist) => matchesQuery(playlist, q));
}

export async function getPlaylistById(id) {
  return await base44.entities.Playlist.get(id);
}

export async function createPlaylist(data) {
  return await base44.entities.Playlist.create({
    track_ids: [],
    ...data,
  });
}

export async function updatePlaylist(id, data) {
  return await base44.entities.Playlist.update(id, data);
}

export async function deletePlaylist(id) {
  await base44.entities.Playlist.delete(id);
}

/** Append a track id to playlist.track_ids (no-op if already present). */
export async function addTrackToPlaylist(playlistId, trackId) {
  const playlist = await base44.entities.Playlist.get(playlistId);
  const trackIds = [...(playlist.track_ids || [])];
  if (!trackIds.includes(trackId)) {
    trackIds.push(trackId);
    return await base44.entities.Playlist.update(playlistId, {
      track_ids: trackIds,
    });
  }
  return playlist;
}

/** Remove a track id from playlist.track_ids. */
export async function removeTrackFromPlaylist(playlistId, trackId) {
  const playlist = await base44.entities.Playlist.get(playlistId);
  const trackIds = (playlist.track_ids || []).filter((id) => id !== trackId);
  return await base44.entities.Playlist.update(playlistId, {
    track_ids: trackIds,
  });
}
