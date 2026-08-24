# MeloTunez Frontend

React + Tailwind dashboard for MeloTunez. Talks to the **Express** wrapper in `../melotunez-backend` (React → Express → Base44). The Base44 `api_key` is never shipped to the browser.

**Direction:** keep Base44 for music entities only; AI/build goes to a pluggable provider — see [`docs/melotunez-direction.md`](../docs/melotunez-direction.md). Chrome side panel scaffold: [`melotunez-extension/`](../melotunez-extension/).

## Stack

- Vite + React 19
- Tailwind CSS v4
- Fetch helpers → Express REST (`/api/*`)

## Prerequisites

Start the backend first:

```bash
cd ../melotunez-backend
npm install
npm start
# listens on http://0.0.0.0:3001
```

## Run

```bash
cd melotunez-frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to `http://127.0.0.1:3001`.

### Production API host

Set `VITE_API_BASE` to your deployed Express URL (no trailing slash), e.g.:

```bash
VITE_API_BASE=https://melotunez-api.onrender.com npm run build
```

## Features

- Sidebar / mobile nav: Tracks, Playlists, Users, Assistant
- Track CRUD + search
- **Playlist detail** — click a playlist → track list, add/remove tracks, create playlist
- **User admin** — Create user (invite) / Delete via Express `/api/users` (server `api_key`)
- **Assistant chat** — wired to Express `POST /api/assistant` (+ `/chat`); prefers pluggable OpenRouter/Ollama when `AI_*` is set on the backend; otherwise Base44 `assistantChat`, with a clear “unavailable” error if neither works
- Persistent bottom audio player for `track.audio_url`
- Loading and error states

### Try in the UI

| Feature | Where |
| --- | --- |
| Playlist detail | **Playlists** → click a card → add/remove tracks; **Create playlist** on the list view |
| User create/delete | **Users** → **Create user** / **Delete** on a row |
| Assistant | **Assistant** → type a message → **Send** |

Optional for Assistant (backend env): `AI_API_KEY` + `AI_PROVIDER=openrouter`, or `AI_PROVIDER=ollama` with a local Ollama server.

## What landed in this dashboard pass

Already present from earlier Option 2 work: nav + components for Tracks / Playlists / Users / Assistant, Express API clients, playlist detail with membership, user invite/delete.

Newly hardened / wired here:

- Backend pluggable AI adapter (`melotunez-backend/src/aiChat.js`) and assistant preference for OpenRouter/Ollama when configured
- Alias route `POST /api/assistant` (same handler as `/api/assistant/chat`)
- Assistant UI graceful “unavailable” messaging + provider footnote on pluggable replies
- Option 3 SDK helpers under `src/sdk/` (reference only; production stays on Express)

## Layout

```
src/
  lib/http.js          # fetch + query helper (Option 2 — preferred)
  api/tracks.js
  api/playlists.js
  api/users.js
  api/assistant.js
  sdk/                 # Option 3 — direct Base44 SDK (optional; not wired to App)
    lib/base44.js
    api/tracks.js
    api/playlists.js
    api/users.js
    api/assistant.js
    App.Truetunes.jsx  # reference monolith only
  components/Tracks.jsx
  components/Playlists.jsx
  components/Users.jsx
  components/Assistant.jsx
  components/AudioPlayer.jsx
  App.jsx
```

See [`src/sdk/README.md`](./src/sdk/README.md) for Option 3 usage and the SDK `list` signature fix.
