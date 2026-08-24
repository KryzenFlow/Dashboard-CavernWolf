# MeloTunez Backend

Express REST wrapper around the MeloTunez Base44 music streaming API.

The Base44 `api_key` lives only on this server. The React frontend should call these routes — not the Base44 SDK directly.

## Stack

- Node.js 18+
- Express 5
- `@base44/sdk`
- CORS enabled
- Binds `0.0.0.0:$PORT` (Render-compatible)

## Setup

```bash
cd melotunez-backend
npm install
npm start
# or: npm run dev   # auto-reload via node --watch
```

Default URL: http://localhost:3001

### Optional env

| Variable | Default |
| --- | --- |
| `PORT` | `3001` |
| `HOST` | `0.0.0.0` |
| `BASE44_APP_ID` | `6a8bbac67d8d3dfc43538a00` |
| `BASE44_API_KEY` | (bundled default; override in production) |

## Endpoints

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/health` | Liveness + app id |
| GET | `/api/tracks` | `?q=&limit=&skip=&sort=` |
| GET | `/api/tracks/:id` | |
| POST | `/api/tracks` | body: Track fields |
| PUT | `/api/tracks/:id` | |
| DELETE | `/api/tracks/:id` | |
| GET | `/api/playlists` | |
| GET | `/api/playlists/:id` | |
| POST | `/api/playlists` | |
| PUT | `/api/playlists/:id` | |
| POST | `/api/playlists/:id/tracks` | `{ "trackId": "..." }` |
| DELETE | `/api/playlists/:id/tracks/:trackId` | |
| DELETE | `/api/playlists/:id` | |
| GET | `/api/users` | |
| POST | `/api/users` | invite / create |
| DELETE | `/api/users/:id` | |
| POST | `/api/assistant/chat` | Base44 `assistantChat` function |

## Layout

```
src/
  base44Client.js   # SDK createClient + api_key
  api.js            # getAllTracks, createPlaylist, …
  server.js         # Express routes
```

## Entity schemas (Base44)

- **Track** — required: `title`, `artist`, `audio_url`; also `album`, `genre`, `duration`, `cover_url`, `plays`
- **Playlist** — required: `name`; also `description`, `cover_url`, `track_ids[]`
- **User** — `email`, `full_name`, `role` (create prefers entity create, falls back to `auth.inviteUser`)

## Quick check

```bash
curl -s http://localhost:3001/api/health
curl -s 'http://localhost:3001/api/tracks?limit=5'
```
