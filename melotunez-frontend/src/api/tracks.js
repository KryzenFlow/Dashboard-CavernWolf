import { base44 } from '../lib/base44.js';

function matchesQuery(record, q, fields) {
  if (!q) return true;
  const term = String(q).toLowerCase().trim();
  if (!term) return true;
  return fields.some((field) =>
    String(record?.[field] ?? '').toLowerCase().includes(term)
  );
}

export async function getAllTracks(options = {}) {
  const { q, limit = 50, skip = 0, sort_by = '-created_date' } = options;
  const records = await base44.entities.Track.list(sort_by, limit, skip);
  return (records || []).filter((track) =>
    matchesQuery(track, q, ['title', 'artist', 'album', 'genre'])
  );
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
