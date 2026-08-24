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

Left **wall of names** tags also filter the library (Bush, Toledo, Frankies, Mom, sax, River Breeze, etc.).

## UI map

- **Left:** Frankie's Wall brand + wall-of-names tags + import
- **Center:** Now playing (album art + handwritten note) + library / wall / edit
- **Bottom:** Progress bar styled like a **BMX rail**

## Permissions

- `storage` / `unlimitedStorage` — save track metadata and tags locally
- `sidePanel` — UI in Chrome’s side panel

No host permissions. No network calls for music.

## Tech

Vanilla HTML / CSS / JS (Manifest V3). Handwritten notes use a **bundled** Patrick Hand font (`fonts/PatrickHand-Regular.ttf`) — no CDN at runtime.
