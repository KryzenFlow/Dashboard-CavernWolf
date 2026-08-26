# Dashboard CavernWolf — Hermes Studio

Containerized Hermes Agent dashboard extracted and completed from Copilot conversation exports.

> **Governance:** All work in this repo operates under the [Trust Discipline Framework](soul.md).
> Load `soul.md` first, then `CI.md`, before any agent or human session. See [AGENTS.md](AGENTS.md).

## Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Static HTML + CSS + JS (`frontend/`) — GitHub Pages or any static host |
| **Backend** | Python FastAPI + WebSocket (`backend/`) — mock mode by default |
| **Clinic module** | CockroachDB schemas + BAA compliance docs (`clinic/`) |
| **Optional** | Docker Compose for backend + frontend |

## Project layout

```
Dashboard-CavernWolf/
├── soul.md            Trust Discipline Framework (root context — load first)
├── CI.md              Cognitive Interface — session lifecycle & behavior
├── AGENTS.md          Cloud / IDE agent onboarding
├── .cursorrules       Global agent instructions for this repo
├── infra/             Secure agent (Docker) + Vultr API v1 (manual-aligned)
│   ├── secure-agent/  Bitwarden + agent_runner.sh
│   └── vultr/         API client, lifecycle, MANUAL_ALIGNMENT.md
├── app/               Security: audit Merkle + supervisor gate pipeline
├── frontend/          index.html, styles.css, script.js
├── backend/           FastAPI web gateway + REST API
├── clinic/            BAA checklist, SQL schemas, sandbox compose
├── source/            Notes about original monolithic exports
├── docker-compose.yml
└── README.md
```

## Governance (Trust Discipline Framework)

| Document | Role |
|----------|------|
| [soul.md](soul.md) | Constitution — intent, motive, follow-through; operating requirements |
| [CI.md](CI.md) | Cognitive Interface — boot lifecycle, escalation, audit sealing |
| [.cursorrules](.cursorrules) | Repo-wide agent rules |
| [AGENTS.md](AGENTS.md) | Initialization order for cloud and IDE agents |

soul.md governs. CI.md implements. When they conflict, surface it — never resolve silently for convenience.

## Audit ledger (Merkle root seal)

Session-scoped tamper-evident audit trail in `app/security/merkle.py`:

```powershell
cd /workspace
$env:PYTHONPATH = "."
python3 -m app.security.merkle          # self-test
python3 -m unittest backend.tests.test_audit_ledger -v
```

Boot loads `soul.md` + `CI.md` as root context; shutdown calls `terminate_session()` to seal and persist the Merkle root to SQL (`audit_ledger` table — schema in `merkle.py` header).

## Secure agent sandbox

Ephemeral agents with Bitwarden secrets, Docker network allowlisting, and encrypted logs.
Production target: **Vultr VPS** (Docker-only).

```bash
export BW_SESSION=$(bw unlock --raw)
cd infra/secure-agent && ./agent_runner.sh
```

Vultr bootstrap: [infra/secure-agent/README.md](infra/secure-agent/README.md#vultr-vps-deployment).
API alignment: [infra/vultr/MANUAL_ALIGNMENT.md](infra/vultr/MANUAL_ALIGNMENT.md) ↔ `source/vultr-api-reference-v1.pdf`.

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

## Frontend build (static deploy / GitHub Pages)

```powershell
cd frontend
npm run build
```

Output: `frontend/dist/` — upload to GitHub Pages or any static host.

Set API URLs when backend is on a different host:

```html
<script>
  window.HERMES_API_BASE = "https://your-api.example.com";
  window.HERMES_WS_URL = "wss://your-api.example.com/ws";
</script>
```

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
