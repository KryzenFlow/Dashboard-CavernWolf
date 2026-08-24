import { apiRequest, buildQuery } from '../lib/http.js';

export async function getAllPlaylists(options = {}) {
  const { q, query, limit = 50, skip = 0, sort, sort_by } = options;
  return apiRequest(
    `/api/playlists${buildQuery({
      q: q ?? query,
      limit,
      skip,
      sort: sort ?? sort_by,
    })}`,
  );
}

export async function getPlaylistById(id) {
  return apiRequest(`/api/playlists/${encodeURIComponent(id)}`);
}

export async function createPlaylist(data) {
  return apiRequest('/api/playlists', { method: 'POST', body: data });
}

export async function updatePlaylist(id, data) {
  return apiRequest(`/api/playlists/${encodeURIComponent(id)}`, {
    method: 'PUT',
    body: data,
  });
}

export async function deletePlaylist(id) {
  return apiRequest(`/api/playlists/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}

export async function addTrackToPlaylist(playlistId, trackId) {
  return apiRequest(
    `/api/playlists/${encodeURIComponent(playlistId)}/tracks`,
    { method: 'POST', body: { trackId } },
  );
}

export async function removeTrackFromPlaylist(playlistId, trackId) {
  return apiRequest(
    `/api/playlists/${encodeURIComponent(playlistId)}/tracks/${encodeURIComponent(trackId)}`,
    { method: 'DELETE' },
  );
}
