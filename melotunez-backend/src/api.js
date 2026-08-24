/**
 * MeloTunez Base44 entity / function wrappers.
 *
 * SDK list signature is list(sort, limit, skip, fields).
 * Option 2's getAll*(query, limit, skip, sort) maps onto that and applies
 * client-side text filtering for `query` when provided.
 */
import { base44 } from './base44Client.js';

function matchesQuery(record, query, fields) {
  if (!query) return true;
  const term = String(query).toLowerCase().trim();
  if (!term) return true;
  return fields.some((field) =>
    String(record?.[field] ?? '')
      .toLowerCase()
      .includes(term),
  );
}

function normalizeListArgs(query, limit, skip, sort) {
  // Support both positional args and a single options object.
  if (query && typeof query === 'object' && !Array.isArray(query)) {
    const opts = query;
    return {
      query: opts.query ?? opts.q ?? '',
      limit: opts.limit ?? 50,
      skip: opts.skip ?? 0,
      sort: opts.sort ?? opts.sort_by ?? '-created_date',
    };
  }
  return {
    query: query ?? '',
    limit: limit ?? 50,
    skip: skip ?? 0,
    sort: sort ?? '-created_date',
  };
}

// ─── Tracks ───────────────────────────────────────────────────────────────────

/** List tracks. Optional `query` filters title/artist/album/genre client-side. */
export async function getAllTracks(query, limit, skip, sort) {
  const args = normalizeListArgs(query, limit, skip, sort);
  const records = await base44.entities.Track.list(
    args.sort,
    args.limit,
    args.skip,
  );
  return (records || []).filter((track) =>
    matchesQuery(track, args.query, ['title', 'artist', 'album', 'genre']),
  );
}

export async function getTrackById(id) {
  return base44.entities.Track.get(id);
}

export async function createTrack(data) {
  return base44.entities.Track.create(data);
}

export async function updateTrack(id, data) {
  return base44.entities.Track.update(id, data);
}

export async function deleteTrack(id) {
  await base44.entities.Track.delete(id);
  return { ok: true, id };
}

// ─── Playlists ────────────────────────────────────────────────────────────────

export async function getAllPlaylists(query, limit, skip, sort) {
  const args = normalizeListArgs(query, limit, skip, sort);
  const records = await base44.entities.Playlist.list(
    args.sort,
    args.limit,
    args.skip,
  );
  return (records || []).filter((playlist) =>
    matchesQuery(playlist, args.query, ['name', 'description']),
  );
}

export async function getPlaylistById(id) {
  return base44.entities.Playlist.get(id);
}

export async function createPlaylist(data) {
  return base44.entities.Playlist.create({
    track_ids: [],
    ...data,
  });
}

export async function updatePlaylist(id, data) {
  return base44.entities.Playlist.update(id, data);
}

export async function deletePlaylist(id) {
  await base44.entities.Playlist.delete(id);
  return { ok: true, id };
}

/** Append a track id to playlist.track_ids (no-op if already present). */
export async function addTrackToPlaylist(playlistId, trackId) {
  const playlist = await base44.entities.Playlist.get(playlistId);
  const trackIds = [...(playlist.track_ids || [])];
  if (!trackIds.includes(trackId)) {
    trackIds.push(trackId);
    return base44.entities.Playlist.update(playlistId, { track_ids: trackIds });
  }
  return playlist;
}

/** Remove a track id from playlist.track_ids. */
export async function removeTrackFromPlaylist(playlistId, trackId) {
  const playlist = await base44.entities.Playlist.get(playlistId);
  const trackIds = (playlist.track_ids || []).filter((id) => id !== trackId);
  return base44.entities.Playlist.update(playlistId, { track_ids: trackIds });
}

// ─── Users ────────────────────────────────────────────────────────────────────

export async function getAllUsers(query, limit, skip, sort) {
  const args = normalizeListArgs(query, limit, skip, sort);
  const records = await base44.entities.User.list(
    args.sort,
    args.limit,
    args.skip,
  );
  return (records || []).filter((user) =>
    matchesQuery(user, args.query, ['full_name', 'email', 'role']),
  );
}

/**
 * Create a user. Prefer entities.User.create (works with api_key).
 * Fall back to auth.inviteUser when entity create is rejected.
 */
export async function createUser(data) {
  const email = data.email || data.user_email;
  const role = data.role || 'user';
  const full_name = data.full_name || '';

  try {
    return await base44.entities.User.create({ email, full_name, role });
  } catch {
    await base44.auth.inviteUser(email, role);
    const users = await base44.entities.User.filter({ email });
    const created = users?.[0];
    if (created?.id && full_name) {
      return base44.entities.User.update(created.id, { full_name });
    }
    return created ?? { email, role, full_name };
  }
}

export async function deleteUser(id) {
  await base44.entities.User.delete(id);
  return { ok: true, id };
}

// ─── Assistant ────────────────────────────────────────────────────────────────

/**
 * Invoke the Base44 assistantChat backend function.
 * SDK surface is functions.invoke(name, data); exposed here as assistantChat(payload).
 */
export async function assistantChat(payload) {
  if (typeof base44.functions.assistantChat === 'function') {
    return base44.functions.assistantChat(payload);
  }
  const result = await base44.functions.invoke('assistantChat', payload || {});
  // axios-style responses nest data; unwrap when present
  return result?.data ?? result;
}
