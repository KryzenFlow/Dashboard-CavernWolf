# BUILD_STATUS.md

Honest status: **Dashboard CavernWolf** vs **VELLORAE MASTER BLUEPRINT v2.3**  
Updated: 2026-07-01

## Runtime status (this laptop)

| Check | Status | Notes |
|-------|--------|-------|
| Docker installed | ✅ | v29.5.3 |
| Stack running | ❌ | `docker compose ps` — no containers up |
| Backend tests | ⚠️ | venv exists; `pytest` not installed in venv |
| OneDrive data link | ❓ | Run `scripts/setup_onedrive_data.ps1` if not done |

**To go green:** `.\scripts\start_minimal.ps1` then `.\scripts\verify_stack.ps1`

---

## Blueprint → repo mapping

| Blueprint component | Target in blueprint | Dashboard-CavernWolf status |
|---------------------|---------------------|----------------------------|
| Supervisor agent | `01_Supervisor_Agent/` | 🟡 `backend/agents/orchestration/pipeline.py` — partial |
| VersionEvaluator | `02_VersionEvaluator/` | ❌ Not implemented |
| Auto-Debugger | `03_Auto_Debugger/` | ❌ Not implemented |
| Ghost Scraper | `04_Ghost_Scraper/` | ❌ Not implemented |
| Local DB | CockroachDB / SQLite | 🟡 SQLite (`data/*.db`) + Chroma; no Cockroach |
| MechIQ | `06_MechIQ_AutoRepair/` | ❌ Lives in OneDrive Grease Monkey folders only |
| Mobile sync | `07_Mobile_Sync/` | ❌ Not implemented |
| Cloud K8s | `08_Cloud_K8s/` | 🟡 `docker-compose.yml`, `.wrangler/` stub |
| Vellorae landing | `09_Vellorae_Landing/` | 🟡 `clinic/`, bleed `vellorae`, prompt file |
| LLaMA 3.2 + 2 13B | dual llama.cpp services | 🟡 Single `llama_stub` on 8080; profile for real llama |
| Qdrant memory | port 6333 | ❌ Using Chroma instead |
| Redis orchestration | rules in Redis | 🟡 Redis present; orchestrator rules API not full |
| LangGraph + SqliteSaver | supervisor graph | ❌ Spec in docs; not in runtime |
| Deployment + rollback | Pushover alerts | ❌ Not wired |
| Base44 SDK apps | external | 🟡 Documented in blueprint only |
| VSIX Agent Claw | Visual Studio | 🟡 `agent_claw/` service; VSIX in OneDrive workspace |
| VIP webhooks | vip.vellorae.org | ❌ Not configured |

Legend: ✅ done · 🟡 partial · ❌ missing · ❓ unknown

---

## Services (docker-compose.yml)

| Service | Port | Status |
|---------|------|--------|
| hermes-studio | 3000 | 🟡 Frontend exists; needs stack up |
| ops-studio | 3001 | 🟡 Static serve of ops_dashboard |
| backend | 8000 | 🟡 FastAPI + tests in repo |
| agent-claw | 9000 | 🟡 Execution layer present |
| llama-service | 8080 | 🟡 Stub; `--profile llama-local` for real |
| redis | internal | ✅ In compose |
| chroma | internal | ✅ In compose (not Qdrant) |
| dev-tools | — | ✅ Node + hermes-cli profile |

`AGENT_STACK_USE_AI=0` by default — safe for structure validation without token burn.

---

## Four projects — integration status

| Project | Build | Deploy | In Hermes bleed |
|---------|-------|--------|-----------------|
| Dashboard CavernWolf | 🟡 Code complete; stack stopped | Local Docker | N/A (host) |
| Vellorae.org | 🟡 Landing HTML in docs/clinic | Not live on Netlify/CF yet | `vellorae` bleed |
| LocalRankai.net | 🟡 Prototype in OneDrive (HTML + zip) | Unknown | `local-services` bleed |
| MechIQ / Grease Monkey | 🟡 Large OneDrive tree + thin `grease-monkey-ai` | Replit artifacts? | `auto_repair` bleed |

---

## Docs & memory

| Asset | Status |
|-------|--------|
| `SOUL.md` | ✅ |
| `AGENTS.md` | ✅ |
| `docs/VELLORAE_MASTER_BLUEPRINT.md` | ✅ Synced from OneDrive |
| `docs/agent-stack-specs/` (31 files) | ✅ Indexed; merge backlog |
| `docs/reference/desktop-export/` | ✅ With README warnings |
| `.cursor/rules/` | ✅ vellorae-blueprint rule |

---

## Recommended build order

1. **Minimal stack green** — `start_minimal.ps1` + `verify_stack.ps1`
2. **OneDrive memory** — `setup_onedrive_data.ps1`
3. **Vellorae pilot** — `/build` or claw scaffold with `ACTIVE_BLEED=vellorae`
4. **Agent registry UI** — merge specs from `docs/agent-stack-specs/INDEX.md` priority 1–3
5. **MechIQ** — import audio diagnostic module from Grease Monkey (isolated PR)
6. **Qdrant swap** — optional; replace or dual-run with Chroma per blueprint
