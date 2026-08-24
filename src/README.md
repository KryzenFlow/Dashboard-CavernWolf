# Hermes Studio Dash (`src/`)

TypeScript UI for the Tauri desktop shell. Wired to WSL FastAPI:

- `GET /agents` / `POST /agents` / `DELETE /agents/{id}`
- `POST /agents/{id}/route` — specialists return plans; they do not execute
- `GET /system/status` — agents, ports, containers, Tailscale IP (polled)

Components required by `.cursorrules`:

- `AgentPullDown` — talk to one roster agent
- `AgentDelete` — remove a roster instance (last Hermes + Claw stay)
- `SystemStatusBar` — bottom bar: agents, ports, containers, Tailscale

Run: `npm install && npm run dev` from the repo root (Vite on :1420).
Point `VITE_HERMES_API` at the Tailscale (or loopback) Hermes URL.

Specialists propose. Only Hermes routes a cycle to Claw Opus.
This folder is not a mock backend.
