# MeloTunez Frontend

React dashboard for the MeloTunez Base44 music streaming API.

## Stack

- Vite + React
- Tailwind CSS v4
- `@base44/sdk`

## Run

```bash
cd melotunez-frontend
npm install
npm run dev
```

Open http://localhost:5173

## Layout

- `src/lib/base44.js` — Base44 client
- `src/api/` — entity helpers (tracks, playlists, users, assistant)
- `src/components/Tracks.jsx`
- `src/components/Playlists.jsx`
- `src/components/Users.jsx`
- `src/App.jsx` — sidebar shell + audio player wiring
