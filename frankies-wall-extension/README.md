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
| **Mom's Smile** | Playlist filter: vibe `mom_smile`, people “Mom”, or instrument “sax” |

Left **wall of names** tags also filter the library (Bush, Toledo, Frankies, Mom, sax, live, studio, etc.).

## Architecture (6 layers)

Pure JS + CSS + HTML — no framework. No TypeScript required. No cloud dependencies.

| Layer | Role | Location |
|-------|------|----------|
| **UI** | Markup + Frankie's Wall styling | `index.html`, `sidepanel.css` |
| **State** | Current track, filters, playback, fork | `sidepanel.js` |
| **Audio** | Play, pause, scrub, volume, A440 fork | `audio/` |
| **Metadata** | Catalog, tags, vibes | `data/` |
| **Rendering** | Each component owns its UI | `components/` |
| **Utilities** | Filters, DOM, storage | `utils/` |

```
sidepanel/
  index.html              UI
  sidepanel.css           UI
  sidepanel.js            State + boot

  components/             Rendering
    trackList.js          filtered tracks
    nowPlaying.js         art + metadata + grind bar
    frankiesWall.js       wall of names + memories
    tuningFork.js         fork icon + click bind

  data/                   Metadata
    tracks.js
    tags.js
    vibes.js

  audio/
    player.js
    tuningForkAudio.js
    waveform.js

  utils/                  Utilities
    filters.js
    dom.js
    storage.js
```

### State layer (`sidepanel.js`)

```js
const state = {
  currentTrack: null,
  instrumentFilter: "all",
  vibeFilter: "all",
  isPlaying: false,
  tuningForkActive: false,
};
```

### Rendering layer (`components/`)

Each component handles its own UI:

| Component | UI responsibility |
|-----------|-------------------|
| `trackList.js` | Renders filtered tracks into `#trackList` |
| `nowPlaying.js` | Album art, metadata, chips; BMX grind bar animation |
| `frankiesWall.js` | Band names, places, people, memories — sidebar + graffiti |
| `tuningFork.js` | Tuning fork SVG mounts + click → `playTuningFork` |

### Utility layer (`utils/`)

| Module | Role |
|--------|------|
| `filters.js` | Instrument + vibe filtering engine |
| `dom.js` | DOM creation helpers |
| `storage.js` | Saving user preferences + library metadata |

### Metadata layer (`data/`)

```js
// tracks.js
export const tracks = [ /* id, title, artist, file, instrument, vibe */ ];

// tags.js
export const instruments = ["electric", "bass", "sax", "mixed"];

// vibes.js — soul encoded into data
export const vibes = ["river_breeze", "fight_focus", "build_repair", "mom_smile"];
```

## How everything connects

**Instrument tags → filters → track list → now playing**

Click **Sax** → `filters.js` sets `instrumentFilter` → `trackList.js` re-renders → click a track → `nowPlaying.js` shows metadata.

**Tuning fork → audio → icon → now playing**

Click fork → `tuningForkAudio.js` plays A440 → `tuningFork.js` pulses icon + `tuningForkActive` → Now Playing stays centered.

**Frankie's wall → tags → vibes**

Sidebar/graffiti in `frankiesWall.js` reads `tags.js` + `vibes.js` — memories become clickable filters.

**Scrubbing → grind bar**

Drag `#seek` → `nowPlaying.js` animates the BMX rail → `player.js` seeks audio.

## UI map (`index.html` + `sidepanel.css`)

| Region | Elements |
|--------|----------|
| **Sidebar** | Brand + fork logo, wall-of-names tags, import |
| **Now Playing** | Cover art, metadata, transport, `#tuningForkBtn` |
| **Library** | Instrument + vibe + story filters, `#trackList` |
| **BMX rail** | `#seek` grind bar, fork mount, times |

## Permissions

- `storage` / `unlimitedStorage` — save track metadata and tags locally
- `sidePanel` — UI in Chrome’s side panel

No host permissions. No network calls for music.

## Tech

Vanilla HTML / CSS / JS (Manifest V3). All modules attach to `window.FrankiesWall`. Handwritten notes use a **bundled** Patrick Hand font — no CDN at runtime.

Just my story, my music, my architecture.
