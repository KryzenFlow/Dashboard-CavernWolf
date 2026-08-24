import { base44 } from '../lib/base44.js';

export async function getAllPlaylists(options = {}) {
  const { q, limit = 50, skip = 0, sort_by = '-created_date' } = options;
  const records = await base44.entities.Playlist.list(sort_by, limit, skip);
  if (!q) return records || [];
  const term = String(q).toLowerCase().trim();
  return (records || []).filter((playlist) =>
    [playlist.name, playlist.description]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(term))
  );
}

export async function getPlaylistById(id) {
  return await base44.entities.Playlist.get(id);
}

export async function createPlaylist(data) {
  return await base44.entities.Playlist.create(data);
}

export async function updatePlaylist(id, data) {
  return await base44.entities.Playlist.update(id, data);
}

export async function deletePlaylist(id) {
  await base44.entities.Playlist.delete(id);
}

export async function addTrackToPlaylist(playlistId, trackId) {
  const playlist = await base44.entities.Playlist.get(playlistId);
  const trackIds = [...(playlist.track_ids || [])];
  if (!trackIds.includes(trackId)) {
    trackIds.push(trackId);
    return await base44.entities.Playlist.update(playlistId, { track_ids: trackIds });
  }
  return playlist;
}

export async function removeTrackFromPlaylist(playlistId, trackId) {
  const playlist = await base44.entities.Playlist.get(playlistId);
  const trackIds = (playlist.track_ids || []).filter((id) => id !== trackId);
  return await base44.entities.Playlist.update(playlistId, { track_ids: trackIds });
}
