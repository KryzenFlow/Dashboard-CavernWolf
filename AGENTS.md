# AGENTS.md — Dashboard CavernWolf / Vellorae umbrella

Persistent memory for Cursor. Read this before large changes.

## What this repo is

**Dashboard CavernWolf** = **Hermes Stack** — Dockerized multi-agent platform:

- `hermes-studio` (port 3000) — customer-facing dashboard
- `backend` (8000) — FastAPI gateway, reasoning, memory, bleed switching
- `agent-claw` (9000) — build sites, CLI, scaffold templates
- `ops_dashboard` (3001) — private Agent Ops UI
- Redis + Chroma/SQLite memory, LLaMA stub (upgradeable)

Identity and principles: [SOUL.md](SOUL.md)  
Master vision: [docs/VELLORAE_MASTER_BLUEPRINT.md](docs/VELLORAE_MASTER_BLUEPRINT.md)  
Build truth table: [docs/BUILD_STATUS.md](docs/BUILD_STATUS.md)

---

## Four main projects (your concern list)

| # | Project | Domain / brand | Where it lives today | Repo integration |
|---|---------|----------------|----------------------|------------------|
| 1 | **Hermes / Dashboard CavernWolf** | Internal ops + studio | `E:\Dashboard-CavernWolf` | **This repo** — source of truth |
| 2 | **Vellorae.org** | Clinic agency umbrella | OneDrive `Project Folder…/Vellorae`, `docs/business-plan/` | Bleed `vellorae` + `backend/agents/prompts/vellorae_clinic.txt` |
| 3 | **LocalRankai.net** | Local SEO monitor + content | OneDrive `Greese Mokey Auto Repair AI\` (80k+ files, incl. node_modules) | Bleed `local-services`; HTML export in that folder |
| 4 | **MechIQ / Grease Monkey** | Auto repair AI (audio/AR) | OneDrive `grease-monkey-ai\`, `Car repairGuide2.3\`, `AutoMate_AI\` | Bleed `auto_repair` in manifest; not merged into backend yet |

**Do not duplicate** the 80k-file Grease Monkey tree into this repo. Import only curated apps/packages when ready.

---

## OneDrive workspace triage

Desktop path: `C:\Users\BossMan\OneDrive\Desktop\New Project Workspace`

| Folder | Action |
|--------|--------|
| `.VELLORAE_MASTER_BLUEPRINT.md.txt` | Synced → `docs/VELLORAE_MASTER_BLUEPRINT.md` |
| `Data for Dashboard…` | Run `scripts/sync_desktop_reference.ps1` → `docs/reference/desktop-export/` |
| `Setting Up Your Agent Stack in Cursor` | Reference only; use repo `scripts/setup_stack.ps1` |
| `2nd Dashboard` | Chat exports — archive or merge into docs |
| `Greese Mokey Auto Repair AI` | Keep as LocalRank/MechIQ monorepo until split |
| `grease-monkey-ai` | Thin monorepo stub — candidate to merge with MechIQ |
| `Mutating Patch Agents for Data base` | Blueprint DB schema — wire into `backend/agents/memory/` |
| `Cockroach plans` | Future prod DB — not wired in compose yet |

---

## Bleed switching (verticals without code edits)

Config: `shared/workflows/bleed-manifest.yaml`  
Env: `ACTIVE_BLEED=doctors|vellorae|local-services|auto_repair|saas|real-estate`

Public studio only shows bleeds with `public: true`.

---

## Commands (use these, not old chat exports)

```powershell
cd E:\Dashboard-CavernWolf

# Full stack
.\scripts\setup_stack.ps1

# Minimal (backend + claw, no token burn)
.\scripts\start_minimal.ps1

# Health check (stack must be running)
.\scripts\verify_stack.ps1

# OneDrive-backed DBs (memory.db, research.db, content.db)
.\scripts\setup_onedrive_data.ps1

# Re-sync desktop reference dumps
.\scripts\sync_desktop_reference.ps1
```

---

## Architecture rules (from blueprint)

- Supervisor + specialist agents; LangGraph-style orchestration target
- Bug tags: `[SYN]` `[DEP]` `[LOG]` `[SEC]` `[MEM]`
- Base44: `functions.invoke`, `entities.filter`, `loginViaEmailPassword` only
- VIP webhooks → `vip.vellorae.org` for critical deploys
- Tailwind for customer-facing HTML; static-export default for clinic pilots

---

## Agent registry (8 roles)

YAML: `shared/agents/registry.yaml`  
Python loader: `backend/agents/registry.py`

Agents: reasoning-tools, reasoning-01, hermes-orca, claw-core, memory-store, content-writer, seo-scanner, redis-bridge.

---

## What NOT to paste from desktop exports

See `docs/reference/README.md` — old FastAPI snippets, `HERMES_MOCK=1`, and superseded `setupstack.sh` are **outdated**.

---

## Suggested next work (priority)

1. Start minimal stack + `verify_stack.ps1` on this laptop
2. Run `setup_onedrive_data.ps1` so memory survives machine swaps
3. Publish Vellorae landing from `clinic/` or scaffold via Agent Claw bleed `vellorae`
4. Curate MechIQ audio module from Grease Monkey folder → `backend/` or separate package
5. Merge Qdrant from blueprint (currently Chroma in compose) when vector memory is needed
