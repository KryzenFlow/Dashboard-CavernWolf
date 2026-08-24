/**
 * Express REST wrapper around MeloTunez Base44 API helpers.
 * Binds 0.0.0.0:$PORT for Render / cloud host compatibility.
 */
import cors from 'cors';
import express from 'express';
import { getAiConfig, isPluggableAiConfigured } from './aiChat.js';
import * as api from './api.js';
import { base44Config } from './base44Client.js';

const app = express();
const PORT = Number(process.env.PORT) || 3001;
const HOST = process.env.HOST || '0.0.0.0';

app.use(cors());
app.use(express.json({ limit: '2mb' }));

/** Uniform async route error handling. */
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

function parseListQuery(req) {
  return {
    query: req.query.q ?? req.query.query ?? '',
    limit: req.query.limit ? Number(req.query.limit) : 50,
    skip: req.query.skip ? Number(req.query.skip) : 0,
    sort: req.query.sort ?? req.query.sort_by ?? '-created_date',
  };
}

// ─── Health ───────────────────────────────────────────────────────────────────

app.get('/health', (_req, res) => {
  res.json({
    ok: true,
    service: 'melotunez-backend',
    appId: base44Config.appId,
  });
});

app.get('/api/health', (_req, res) => {
  const ai = getAiConfig();
  res.json({
    ok: true,
    service: 'melotunez-backend',
    appId: base44Config.appId,
    mode: 'api_key',
    assistant: {
      pluggableConfigured: isPluggableAiConfigured(),
      provider: ai.provider,
      model: ai.model,
    },
  });
});

// ─── Tracks ───────────────────────────────────────────────────────────────────

app.get(
  '/api/tracks',
  asyncHandler(async (req, res) => {
    const { query, limit, skip, sort } = parseListQuery(req);
    const tracks = await api.getAllTracks(query, limit, skip, sort);
    res.json(tracks);
  }),
);

app.get(
  '/api/tracks/:id',
  asyncHandler(async (req, res) => {
    const track = await api.getTrackById(req.params.id);
    res.json(track);
  }),
);

app.post(
  '/api/tracks',
  asyncHandler(async (req, res) => {
    const track = await api.createTrack(req.body || {});
    res.status(201).json(track);
  }),
);

app.put(
  '/api/tracks/:id',
  asyncHandler(async (req, res) => {
    const track = await api.updateTrack(req.params.id, req.body || {});
    res.json(track);
  }),
);

app.delete(
  '/api/tracks/:id',
  asyncHandler(async (req, res) => {
    const result = await api.deleteTrack(req.params.id);
    res.json(result);
  }),
);

// ─── Playlists ────────────────────────────────────────────────────────────────

app.get(
  '/api/playlists',
  asyncHandler(async (req, res) => {
    const { query, limit, skip, sort } = parseListQuery(req);
    const playlists = await api.getAllPlaylists(query, limit, skip, sort);
    res.json(playlists);
  }),
);

app.get(
  '/api/playlists/:id',
  asyncHandler(async (req, res) => {
    const playlist = await api.getPlaylistById(req.params.id);
    res.json(playlist);
  }),
);

app.post(
  '/api/playlists',
  asyncHandler(async (req, res) => {
    const playlist = await api.createPlaylist(req.body || {});
    res.status(201).json(playlist);
  }),
);

app.put(
  '/api/playlists/:id',
  asyncHandler(async (req, res) => {
    const playlist = await api.updatePlaylist(req.params.id, req.body || {});
    res.json(playlist);
  }),
);

app.post(
  '/api/playlists/:id/tracks',
  asyncHandler(async (req, res) => {
    const trackId = req.body?.trackId ?? req.body?.track_id;
    if (!trackId) {
      res.status(400).json({ error: 'trackId is required' });
      return;
    }
    const playlist = await api.addTrackToPlaylist(req.params.id, trackId);
    res.json(playlist);
  }),
);

app.delete(
  '/api/playlists/:id/tracks/:trackId',
  asyncHandler(async (req, res) => {
    const playlist = await api.removeTrackFromPlaylist(
      req.params.id,
      req.params.trackId,
    );
    res.json(playlist);
  }),
);

app.delete(
  '/api/playlists/:id',
  asyncHandler(async (req, res) => {
    const result = await api.deletePlaylist(req.params.id);
    res.json(result);
  }),
);

// ─── Users ────────────────────────────────────────────────────────────────────

app.get(
  '/api/users',
  asyncHandler(async (req, res) => {
    const { query, limit, skip, sort } = parseListQuery(req);
    const users = await api.getAllUsers(query, limit, skip, sort);
    res.json(users);
  }),
);

app.post(
  '/api/users',
  asyncHandler(async (req, res) => {
    const user = await api.createUser(req.body || {});
    res.status(201).json(user);
  }),
);

app.delete(
  '/api/users/:id',
  asyncHandler(async (req, res) => {
    const result = await api.deleteUser(req.params.id);
    res.json(result);
  }),
);

// ─── Assistant ────────────────────────────────────────────────────────────────

app.post(
  '/api/assistant',
  asyncHandler(async (req, res) => {
    const result = await api.assistantChat(req.body || {});
    res.json(result);
  }),
);

app.post(
  '/api/assistant/chat',
  asyncHandler(async (req, res) => {
    const result = await api.assistantChat(req.body || {});
    res.json(result);
  }),
);

// ─── Errors ───────────────────────────────────────────────────────────────────

app.use((err, _req, res, _next) => {
  console.error('[melotunez-backend]', err?.message || err);
  const status =
    err?.status ||
    err?.response?.status ||
    (err?.message?.includes('not found') ? 404 : 500);
  let message =
    err?.message ||
    err?.response?.data?.message ||
    err?.response?.data?.error ||
    'Internal server error';
  if (message && typeof message === 'object') {
    message = message.message || JSON.stringify(message);
  }
  res.status(Number(status) || 500).json({
    error: String(message),
    code: err?.code || undefined,
  });
});

app.listen(PORT, HOST, () => {
  console.log(`MeloTunez API listening on http://${HOST}:${PORT}`);
  console.log(`Health: http://${HOST}:${PORT}/api/health`);
});
