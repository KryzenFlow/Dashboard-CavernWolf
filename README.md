# Dashboard CavernWolf — Hermes Stack

Production unified compose: **Hermes Studio** dashboard, **multi-agent backend** (reasoning, memory, LlamaIndex orchestration), **Agent Claw** execution layer, **LLaMA stub** (upgradeable to llama.cpp), and **dev-tools** for template workflows.

See [SOUL.md](SOUL.md) for agent identity and principles.

## Stack

| Service | Port | Role |
|---------|------|------|
| `hermes-studio` | 3000 | Hermes Studio dashboard ([`frontend/`](frontend/)) |
| `backend` | 8000 | FastAPI gateway + `/reason`, `/action`, `/memory`, WebSocket |
| `agent-claw` | 9000 | Execution layer — build sites, CLI, scaffold templates |
| `llama-service` | 8080 | LLaMA stub (`/completion`); use `--profile llama-local` for real llama.cpp |
| `dev-tools` | — | Node + **hermes-cli**, gh, docker, vite, netlify, vercel |
| `redis` | internal | Short-term memory |
| `chroma` | internal | Long-term semantic memory |

## Quick start

### One command (easiest)

```powershell
cd E:\Dashboard-CavernWolf
powershell -ExecutionPolicy Bypass -File .\scripts\setup_stack.ps1
```

Creates folders, copies `.env`, validates Docker, and starts the stack. See [scripts/README.md](scripts/README.md).

### Manual

```powershell
cp .env.example .env
docker compose up --build
```

- Studio: http://localhost:3000
- Backend: http://localhost:8000/health
- Agent Claw: http://localhost:9000/health

### Chat commands

- Normal message → reasoning via WebSocket or `POST /reason`
- `/build` → scaffold static site to `shared/workflows/site`
- `/action {"action":"build_website","params":{"template":"static-site"}}` → REST action via claw

### Customer workflows (Agent Claw)

| Action | Example `/action` body |
|--------|-------------------------|
| Scaffold template | `{"action":"scaffold","params":{"template":"static-site","project":"demo"}}` |
| Build website | `{"action":"build_website","params":{"template":"static-site","output_dir":"/shared/workflows/site"}}` |
| Deploy GitHub Pages | `{"action":"deploy_github_pages","params":{"site_dir":"/shared/workflows/site","repo_url":"https://github.com/user/repo.git"}}` |
| Package Docker app | `{"action":"package_docker_app","params":{"app_dir":"/shared/workflows/demo","image_name":"customer/demo:v1"}}` |
| Trigger webhook CI | `{"action":"trigger_ci_cd","params":{"webhook_url":"https://ci.example.com/hook","payload":{"branch":"main"}}}` |
| Trigger GitHub Actions | `{"action":"trigger_ci_cd","params":{"workflow":"pages.yml","ref":"main"}}` |

Set `GITHUB_TOKEN` in `.env` for git/gh deploy (never commit the token).

**End-to-end example (curl):**

```powershell
# 1. Build site from template
curl -X POST http://localhost:9000/execute -H "Content-Type: application/json" -d "{\"action\":\"build_website\",\"params\":{\"template\":\"static-site\",\"output_dir\":\"/shared/workflows/site\"}}"

# 2. Deploy to gh-pages (token from .env or embedded in repo_url)
curl -X POST http://localhost:9000/execute -H "Content-Type: application/json" -d "{\"action\":\"deploy_github_pages\",\"params\":{\"site_dir\":\"/shared/workflows/site\"}}"

# 3. Package as Docker image
curl -X POST http://localhost:9000/execute -H "Content-Type: application/json" -d "{\"action\":\"package_docker_app\",\"params\":{\"app_dir\":\"/shared/workflows/site\",\"image_name\":\"customer/site:v1\"}}"
```

## Project layout

```
Dashboard-CavernWolf/
├── SOUL.md
├── docker-compose.yml
├── backend/           # Hermes gateway + agents (reasoning, memory, orchestration)
├── agent_claw/        # Execution layer
├── llama_stub/        # Default LLaMA-compatible stub
├── frontend/          # Hermes Studio UI
├── templates/         # Website/app starter kits
├── shared/workflows/  # Generated customer projects
├── data/              # SQLite memory DB
└── models/            # GGUF models (for llama-local profile)
```

## Environment

Copy [`.env.example`](.env.example) to `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_STACK_ENABLED` | `1` | Route chat through agent orchestration |
| `LLM_PROVIDER` | `mock` | `mock`, `llama`, `ollama`, or `api` |
| `CLAW_URL` | `http://agent-claw:9000` | Agent Claw base URL |
| `MEMORY_DB_URL` | `sqlite:////data/memory.db` | Structured memory |
| `GIT_REPO_ROOT` | `/repo` | Git panel cwd in Docker |

## Architecture: public Studio vs internal Agent Ops

| Layer | Audience | What it exposes |
|-------|----------|-----------------|
| **Hermes Studio** (`STUDIO_MODE=public`, port 3000) | Customers, GitHub | Whitelisted CLI only |
| **Agent Ops** (`STUDIO_MODE=internal`, port 3001) | You only | `/ops/*`, `/api/seo`, research job queue, all bleeds |

**Other computer:** run backend with `STUDIO_MODE=internal` and poll `POST /ops/jobs/claim-and-run` (or `scripts/agent_worker.ps1`). Databases live in `data/` — link to OneDrive with `scripts/setup_onedrive_data.ps1`.

| DB file | Purpose |
|---------|---------|
| `memory.db` | Agent conversation memory |
| `research.db` | SEO / research job queue |
| `content.db` | Blog drafts → publish to `shared/workflows/{project}/blog/` |

Content API (internal): `GET/POST /ops/content/drafts`, `POST /ops/content/generate`, `POST /ops/content/drafts/{id}/publish`

Set `STUDIO_MODE=internal` in `.env` on your private deployment to unlock internal-only bleeds and the full agent API.

### Switch target bleeds (no code changes)

Edit [`shared/workflows/bleed-manifest.yaml`](shared/workflows/bleed-manifest.yaml) or set one env var:

```bash
ACTIVE_BLEED=saas-b2b   # dental | auto-repair | local-services | …
```

Studio loads industry, template, deploy profile, pain points, and Quick Actions from the manifest. Add a new bleed block in YAML — do not hardcode verticals in Python or the UI.

API: `GET /studio/bleeds`, `POST /studio/bleed/select`

## Reversible deploy workflows (no AI / no tokens by default)

Studio **Projects** tab uses [`shared/workflows/deploy-profiles.yaml`](shared/workflows/deploy-profiles.yaml). Switch targets without code changes:

```bash
# In .env — default: zip static site for Namecheap FTP (no tokens)
DEPLOY_PROFILE=static-export
HERMES_CLI_BRIDGE=claw
AGENT_STACK_USE_AI=0
```

| Profile | Tokens needed | Best for |
|---------|---------------|----------|
| `static-export` | None | Namecheap / FTP / any host |
| `github-pages` | Optional `GITHUB_TOKEN` | GitHub Pages |
| `docker` | None | Railway / Azure Container Apps image |
| `railway` | `RAILWAY_TOKEN` | Railway deploy |
| `azure-static` | `AZURE_STORAGE_*` | Azure blob / static site |
| `cockroach-sandbox` | None | Local clinic DB sandbox |

API: `GET /studio/profiles`, `POST /studio/deploy`, `POST /studio/cli/run`

## hermes-cli (dev-tools)

Unified CLI inside the `dev-tools` container:

```bash
docker compose exec dev-tools hermes-cli --help
docker compose exec dev-tools hermes-cli new site --template static-site --name mysite
docker compose exec dev-tools hermes-cli deploy github --name mysite
docker compose exec dev-tools hermes-cli suggest --industry "real estate"
docker compose exec dev-tools hermes-cli tools
```

Hermes Studio **Projects** tab calls the same flows via `/studio/new-website` and `/studio/deploy`.

Optional: install Supabase/Firebase/n8n in dev-tools with `pip`/`npm` as needed.

## Real LLaMA (optional)

1. Download a `.gguf` model into `./models/`
2. Set in `.env`: `LLM_PROVIDER=llama`, `LLAMA_URL=http://llama-cpp:8080`
3. Run: `docker compose --profile llama-local up --build`

## GitHub Pages

1. Repo **Settings → Pages → Source**: GitHub Actions
2. Push to `main` — [`.github/workflows/pages.yml`](.github/workflows/pages.yml) deploys `frontend/dist`

## New PC or external drive setup

If you moved the project from another machine (for example on drive `E:\`):

1. **Open this folder in Cursor** — `E:\Dashboard-CavernWolf` (or wherever the repo lives). You do not need to give special repo access; Cursor works on local folders.
2. **Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)** and start it before running compose.
3. **Copy env file** (once): `cp .env.example .env`
4. **Start the stack**: `docker compose up --build`
5. **Push to GitHub** when ready — uncommitted agent-stack files should be committed so GitHub CI and Pages stay in sync.

Old Cursor chat history from the previous PC is optional; the code and plan live in this repo (`SOUL.md`, `docker-compose.yml`, `backend/agents/`, etc.).

## Local dev (without Docker)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:AGENT_STACK_ENABLED="1"
$env:LLM_PROVIDER="mock"
uvicorn main:app --reload
```

```powershell
cd frontend
npm run dev
```

## Clinic module

See [clinic/README.md](clinic/README.md).

## License

Derived from user Copilot exports referencing NousResearch/hermes-agent (Apache/MIT per upstream).
