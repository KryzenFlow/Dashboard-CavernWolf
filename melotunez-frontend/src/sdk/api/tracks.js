/**
 * Option 3 — Track helpers via Base44 SDK (browser).
 *
 * App components should keep using `src/api/tracks.js` (Express proxy).
 * SDK `list` signature is list(sort, limit, skip, fields) — not an options object.
 * Exported API keeps the user's options-object shape; `q` is applied client-side.
 */
import { base44 } from '../lib/base44.js';

function matchesQuery(track, q) {
  if (!q) return true;
  const term = String(q).toLowerCase().trim();
  if (!term) return true;
  return ['title', 'artist', 'album', 'genre'].some((field) =>
    String(track?.[field] ?? '')
      .toLowerCase()
      .includes(term),
  );
}

export async function getAllTracks(options = {}) {
  const { q, limit = 50, skip = 0, sort_by } = options;
  const sort = sort_by ?? '-created_date';
  const records = await base44.entities.Track.list(sort, limit, skip);
  return (records || []).filter((track) => matchesQuery(track, q));
}

export async function getTrackById(id) {
  return await base44.entities.Track.get(id);
}

export async function createTrack(data) {
  return await base44.entities.Track.create(data);
}

export async function updateTrack(id, data) {
  return await base44.entities.Track.update(id, data);
}

export async function deleteTrack(id) {
  await base44.entities.Track.delete(id);
}

export async function bulkCreateTracks(records) {
  return await base44.entities.Track.bulkCreate(records);
}
