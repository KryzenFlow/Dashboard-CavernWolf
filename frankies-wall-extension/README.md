# Frankie's Wall

Local-only Chrome extension for **your personal recordings and albums**. Black-and-white wall aesthetic with a warm amber accent for **Mom's Smile**.

## Local-only disclaimer

Frankie's Wall plays **files you choose on this device**. It does **not**:

- stream from YouTube, Spotify, or any cloud service
- upload audio anywhere
- require Base44 or any external music API
- need host permissions for third-party sites

Only import audio you own or have rights to play personally.

## Load unpacked

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select this folder: `frankies-wall-extension/`
5. Click the extension icon (or pin it) — the **side panel** opens

## Seed catalog

On first load, Frankie's Wall merges the built-in catalog (`sidepanel/data/tracks.js`):

| Track | Artist | Instrument | Vibe (id) |
|-------|--------|------------|-----------|
| Glycerine | Bush | electric | `river_breeze` |
| Sax Live Recording | Drew | sax | `mom_smile` |

Catalog entries use a singular `vibe` id (snake_case). `data/vibes.js` maps ids → wall labels (e.g. `mom_smile` → Mom's Smile).

Drop matching MP3s under `music/` (see `music/README.md`) and reload the extension — they play without re-import. You can still **Import files**; matching filenames attach to catalog IDs and tags stick.

## Import + play

1. **Import files** or **Import folder** (left sidebar)
2. Tracks appear in **Library**
3. Click a track to play (audio stays as a local blob in this session)
4. **Tag** a track: bands, places, people, instruments, vibes, handwritten note, optional local cover image
5. Metadata/tags persist in `chrome.storage.local`. Audio file handles are session-based — if you reopen Chrome later, **re-import the same files/folder** to play again (tags remain)

## Views

| View | What it does |
|------|----------------|
| **Library** | All imported tracks (or current filter) |
| **Frankie's Wall** | Graffiti grid of band / place / people names — click to filter |
| **Mom's Smile** | Playlist filter: vibe “Mom's Smile”, people “Mom”, or instrument “sax” |

Left **wall of names** tags also filter the library (Bush, Toledo, Frankies, Mom, sax, live, studio, etc.).

## Architecture (6 layers)

Pure JS + CSS + HTML — no framework.

| Layer | Role | Location |
|-------|------|----------|
| **UI** | Markup + Frankie's Wall styling | `index.html`, `sidepanel.css` |
| **State** | Library, filters, current track | `sidepanel.js` → `FrankiesWall.state` |
| **Audio** | Play, pause, scrub, volume, A440 fork, optional waveform | `audio/player.js`, `audio/tuningForkAudio.js`, `audio/waveform.js` |
| **Metadata** | Catalog, tags, vibes | `data/tracks.js`, `data/tags.js`, `data/vibes.js` |

### Metadata layer (`data/`)

Seed catalog in `tracks.js` — each entry: `id`, `title`, `artist`, `file`, `instrument`, `vibe` (snake_case id).

```js
export const tracks = [
  { id: "bush_glycerine", title: "Glycerine", artist: "Bush",
    file: "/music/bush/glycerine.mp3", instrument: "electric", vibe: "river_breeze" },
  { id: "drew_sax_live_01", title: "Sax Live Recording", artist: "Drew",
    file: "/music/drew/sax_live_01.mp3", instrument: "sax", vibe: "mom_smile" },
];
```

`vibes.js` maps vibe ids → UI labels. `tags.js` holds wall presets, story filters, and instrument ids:

```js
export const instruments = ["electric", "bass", "sax", "mixed"];
```
| **Rendering** | Track list, wall, now playing | `components/` |
| **Utilities** | DOM, storage, filters | `utils/dom.js`, `utils/storage.js`, `utils/filters.js` |

```
sidepanel/
  index.html
  sidepanel.css
  sidepanel.js          ← orchestrator (State + boot)

  components/
    tuningFork.js
    trackList.js
    nowPlaying.js
    frankiesWall.js

  data/
    tracks.js
    tags.js
    vibes.js

  audio/
    player.js
    tuningForkAudio.js
    waveform.js

  utils/
    dom.js
    storage.js
    filters.js
```

## Story filters (expand anytime)

Edit `sidepanel/data/tags.js` — add filter chips like **live**, **studio**, **mom_mode**, or anything that fits your wall. Reload the extension to pick them up.

## UI map (`index.html` + `sidepanel.css`)

Everything visible lives in the UI layer — black-and-white wall aesthetic, marker buttons, gritty textures.

| Region | Elements |
|--------|----------|
| **Sidebar** | Brand + tuning fork logo mount, wall-of-names tags (bands, places, people, instruments, story, vibes), import buttons |
| **Now Playing** | Cover art cluster + art fork mount, title/note/chips, transport, `#tuningForkBtn` (A440) |
| **Library** | `#instrumentFilter` (Courier marker B&W), `#vibeFilter` (hand-drawn chips, Mom's Smile accent), `#storyFilter` (expandable from `tags.js`), `#trackList` |
| **BMX rail** | `#seek` progress bar, rail fork mount, elapsed/total times, Music Outro |

Tuning fork SVG mounts: `[data-tuning-fork-mount="logo|art|rail"]` plus the Now Playing button.

## Audio layer (`audio/`)

| Capability | Module | Notes |
|------------|--------|-------|
| **Play / pause** | `player.js` | `playTrack`, `togglePlay`, prev/next queue |
| **Scrub** | `player.js` | `#seek` BMX rail → `seekToRatio` |
| **Volume** | `player.js` | `#volume` slider, persisted locally |
| **Tuning fork** | `tuningForkAudio.js` | A440 sine + overtone, 2s fade |
| **Waveform** | `waveform.js` | Optional — click **Wave** in transport |

Transport binds in `player.js`; progress UI updates via `components/nowPlaying.js`.

## Permissions

- `storage` / `unlimitedStorage` — save track metadata and tags locally
- `sidePanel` — UI in Chrome’s side panel

No host permissions. No network calls for music.

## Tech

Vanilla HTML / CSS / JS (Manifest V3). All modules attach to `window.FrankiesWall`. Handwritten notes use a **bundled** Patrick Hand font (`fonts/PatrickHand-Regular.ttf`) — no CDN at runtime.
