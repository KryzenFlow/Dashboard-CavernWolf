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
- Playlist CRUD + add/remove tracks
- User invite / delete
- Assistant chat (Base44 `assistantChat` — migrate to pluggable AI per direction doc)
- Persistent bottom audio player for `track.audio_url`
- Loading and error states

## Layout

```
src/
  lib/http.js          # fetch + query helper
  api/tracks.js
  api/playlists.js
  api/users.js
  api/assistant.js
  components/Tracks.jsx
  components/Playlists.jsx
  components/Users.jsx
  components/Assistant.jsx
  components/AudioPlayer.jsx
  App.jsx
```
