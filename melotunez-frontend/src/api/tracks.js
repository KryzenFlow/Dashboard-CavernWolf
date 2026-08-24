import { apiRequest, buildQuery } from '../lib/http.js';

/**
 * Frontend track helpers — call Express `/api/tracks` (server holds Base44 key).
 */
export async function getAllTracks(options = {}) {
  const { q, query, limit = 50, skip = 0, sort, sort_by } = options;
  return apiRequest(
    `/api/tracks${buildQuery({
      q: q ?? query,
      limit,
      skip,
      sort: sort ?? sort_by,
    })}`,
  );
}

export async function getTrackById(id) {
  return apiRequest(`/api/tracks/${encodeURIComponent(id)}`);
}

export async function createTrack(data) {
  return apiRequest('/api/tracks', { method: 'POST', body: data });
}

export async function updateTrack(id, data) {
  return apiRequest(`/api/tracks/${encodeURIComponent(id)}`, {
    method: 'PUT',
    body: data,
  });
}

export async function deleteTrack(id) {
  return apiRequest(`/api/tracks/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}
