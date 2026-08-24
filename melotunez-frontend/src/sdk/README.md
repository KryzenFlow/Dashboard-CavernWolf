# Option 3 — direct Base44 SDK (optional)

Paste-compatible Base44 client helpers. **Not used by App components.**

| Path | Role |
| --- | --- |
| `lib/base44.js` | `createClient({ appId, headers: { api_key } })` |
| `api/tracks.js` | Track CRUD + `bulkCreateTracks` (SDK `list` args corrected) |
| `api/playlists.js` | Playlist CRUD + add/remove track (SDK `list` args corrected) |
| `api/users.js` | *(next paste)* |

## Preferred path (Option 2)

Production UI imports `src/api/*` → Express `/api` → server Base44 key.

Equivalent server wrappers already live in `melotunez-backend/src/api.js`
(`getAllTracks` accepts either positional args or `{ q, query, limit, skip, sort_by }`).

## SDK `list` fix

Base44 SDK: `entity.list(sort, limit, skip, fields)`.

Option 3 helpers keep the user's `getAllTracks({ q, limit, skip, sort_by })` shape,
call `list(sort_by, limit, skip)`, then filter by `q` on title/artist/album/genre.

## Enable this path

```bash
npm install @base44/sdk
```

Then import from `src/sdk/api/...` instead of `src/api/...` (exposes `api_key` in the bundle — avoid in production).
