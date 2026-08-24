# Option 3 — direct Base44 SDK (optional)

Paste-compatible Base44 client helpers and a **reference** Truetunes App.
**Not used by the production App.** Prefer Option 2 (Express proxy).

| Path | Role |
| --- | --- |
| `lib/base44.js` | `createClient({ appId, headers: { api_key } })` |
| `api/tracks.js` | Track CRUD + `bulkCreateTracks` |
| `api/playlists.js` | Playlist CRUD + add/remove track membership |
| `api/users.js` | User list/CRUD; `createUser` tries entity create then `auth.inviteUser` |
| `api/assistant.js` | `sendAssistantMessage` → `functions.assistantChat` or `invoke` |
| `App.Truetunes.jsx` | Monolithic Option 3 UI paste (Truetunes branding) — reference only |
| `package.snippet.json` | Original Option 3 deps (React 18 / Tailwind 3 / `@base44/sdk`) |

## Preferred path (Option 2)

Production UI: `src/App.jsx` + `src/components/*` import `src/api/*` → Express `/api`
→ server Base44 key (`melotunez-backend`). Do **not** swap `main.jsx` to
`App.Truetunes.jsx` — that paste lacks edit-track, playlist detail, admin users,
and the Assistant panel that production already has.

## SDK `list` fix

Base44 SDK: `entity.list(sort, limit, skip, fields)`.

Option 3 helpers keep the user's `getAll*({ q, limit, skip, sort_by })` shape,
call `list(sort_by, limit, skip)`, then filter by `q` client-side.

## Enable this path (experiments only)

```bash
npm install @base44/sdk
```

Then import from `src/sdk/api/...` (or mount `App.Truetunes.jsx`).
This exposes `api_key` in the browser bundle — avoid in production.
See `package.snippet.json` for the original paste's dependency set; root
`package.json` stays on React 19 + Tailwind 4 for the Express-backed app.
