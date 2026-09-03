# Dashboard CavernWolf — Hermes Studio

Containerized Hermes Agent dashboard extracted and completed from Copilot conversation exports.

## Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Static HTML + CSS + JS (`frontend/`) — Cloudflare Workers (assets) or GitHub Pages |
| **Backend** | Python FastAPI + WebSocket (`backend/`) — mock mode by default |
| **Clinic module** | CockroachDB schemas + BAA compliance docs (`clinic/`) |
| **Optional** | Docker Compose for backend + frontend |

## Project layout

```
Dashboard-CavernWolf/
├── frontend/          index.html, styles.css, script.js
├── backend/           FastAPI web gateway + REST API
├── clinic/            BAA checklist, SQL schemas, sandbox compose
├── source/            Notes about original monolithic exports
├── docker-compose.yml
└── README.md
```

## Quick start (local)

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m web_gateway.entry
```

Backend runs at http://localhost:8000  
Health check: http://localhost:8000/health

### 2. Frontend

```powershell
cd frontend
npm run dev
```

Open http://localhost:3000

### 3. Docker (both services)

```powershell
docker compose up --build
```

## Deploy frontend to Cloudflare (recommended)

The dashboard UI is static HTML/CSS/JS and deploys as an **assets-only Cloudflare Worker**. Your domain(s) must already be added to Cloudflare (DNS hosted or proxied there).

### 1. One-time login

```bash
cd frontend
npx wrangler login
```

### 2. Deploy

```bash
cd frontend
npm install
npm run deploy
```

You get a live URL like `https://cavernwolf-hermes-studio.<your-subdomain>.workers.dev`.

### 3. Attach your custom domain

1. In [Cloudflare Dashboard → Workers & Pages](https://dash.cloudflare.com/?to=/:account/workers-and-pages), open **cavernwolf-hermes-studio**.
2. **Settings → Domains & Routes → Add → Custom Domain**.
3. Enter your domain or subdomain (e.g. `example.com` or `www.example.com`).
4. Cloudflare creates the DNS record for you (zone must already be on your Cloudflare account).

Or edit `frontend/wrangler.jsonc` and uncomment:

```jsonc
"routes": [
  { "pattern": "example.com", "custom_domain": true },
  { "pattern": "www.example.com", "custom_domain": true }
]
```

Then run `npm run deploy` again.

> **Note:** The Python FastAPI backend is not part of this Cloudflare static deploy. Chat/WebSocket features need the API hosted separately (VPS, Railway, etc.). Until then the page still loads; connection status will show offline/local defaults.

### Optional: point API at a remote backend

In `frontend/index.html`, before `script.js`:

```html
<script>
  window.HERMES_API_BASE = "https://your-api.example.com";
  window.HERMES_WS_URL = "wss://your-api.example.com/ws";
</script>
```

## Frontend build (static / GitHub Pages)

```powershell
cd frontend
npm run build
```

Output: `frontend/dist/` — upload to GitHub Pages or any static host.
## Backend environment

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | HTTP port |
| `HERMES_MOCK` | `1` | Mock RPC when full hermes-agent not installed |
| `HERMES_HOME` | `~/.hermes` | Skills/memory directory |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |

## Integrating with real Hermes Agent

This project is designed as a **standalone module**. To connect to [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent):

1. Copy `backend/web_gateway/` into your hermes-agent fork
2. Replace mock `handle_rpc()` with `tui_gateway.server.dispatch()`
3. Set `HERMES_MOCK=0`

## Clinic module

See [clinic/README.md](clinic/README.md) for CockroachDB sandbox and BAA compliance files (split from the second section of the original monolith).

## Source files analyzed

| File | Role |
|------|------|
| `NousResearchhermes-agent.txt with claw need done asap.txt` | Monolith #1: Hermes dashboard + backend design (partial code) |
| `sun_jun_14_2026_containerized_dashboard_for_hermes_agent.json` | Monolith #2: Same conversation as JSON (duplicate) |

## What could not be done

1. **Write to original path** — `e:\Program Files\Project folder\Dashboard CavernWolfprjt1.1\` is read-only (Access denied). Project built at `E:\Dashboard-CavernWolf\` instead.
2. **Full Hermes Agent integration** — Source export lacks complete `web_gateway/app.py` tied to `tui_gateway.server.dispatch()`. Backend runs in mock mode until merged into a hermes-agent fork.
3. **React/Monaco version** — Copilot proposed React + Monaco; implemented static HTML/CSS/JS for GitHub Pages and simple static build compatibility.
4. **OpenClaw/Ollama Docker stack** — Referenced in source but not fully specified; clinic sandbox compose provided separately.

## License

Derived from user Copilot exports referencing NousResearch/hermes-agent (Apache/MIT per upstream).
