# VELLORAE MASTER BLUEPRINT (V2.3 - LocalRankai.net)

**Umbrella:** Vellorae.org (AI agency, VIP portal, clinic pilots)  
**Sub-projects:** LocalRankai.net, MechIQ (AI auto repair — AR/audio)  
**Infrastructure:** Cloudflare (DNS/edge), Render & Railway (Node/microservices), Alibaba Cloud (heavy AI/LLaMA), CockroachDB (global DB), Qdrant (vector memory), Redis (state/cache)

> Canonical copy synced from OneDrive `New Project Workspace\.VELLORAE_MASTER_BLUEPRINT.md.txt`  
> Last synced: 2026-07-01

---

## 1. Cursor global instructions

When operating in this repository:

- **Architecture:** Multi-agent LangGraph-style system. Supervisor + specialist pattern.
- **Agent workflow:** VersionEvaluator → Reasoning → Auto-Debugger → Ghost Scraper → MemoryStore → Deployment.
- **Bug tagging:** Debugger tags bugs: `[SYN]`, `[DEP]`, `[LOG]`, `[SEC]`, `[MEM]` before fixing.
- **VIP alerts:** Critical deployments, bugs, and scores POST webhooks to `vip.vellorae.org`.
- **Base44 SDK:** Use exact method names (`functions.invoke`, `entities.filter`, `loginViaEmailPassword`). Do NOT hallucinate Firebase/Supabase methods.
- **Frontend:** Tailwind CSS. Support HTML/HTMX demos on subdomains (e.g. `demo.vellorae.org`).

---

## 2. Target directory structure (blueprint)

```
My_Mega_Project/
├── .cursorrules
├── 00_Project_Notes/
├── 01_Supervisor_Agent/
├── 02_VersionEvaluator/
├── 03_Auto_Debugger/
├── 04_Ghost_Scraper/
├── 05_Local_Database/
├── 06_MechIQ_AutoRepair/
├── 07_Mobile_Sync/
├── 08_Cloud_K8s/
├── 09_Vellorae_Landing/
└── docker-compose.yml
```

**Implemented as:** `E:\Dashboard-CavernWolf` (Hermes Stack) — see [BUILD_STATUS.md](BUILD_STATUS.md) for mapping.

---

## 3. Orchestration rules (Redis / API)

UI-editable rules at `/api/orchestrator/rules`:

| Agent | Priority | Depends on |
|-------|----------|------------|
| VersionEvaluator | 0 | — |
| ReasoningAgent | 1 | VersionEvaluator |
| WebScraper | 2 | ReasoningAgent |
| MemoryStoreQdrant | 3 | WebScraper |
| DeploymentAgent | 4 | MemoryStoreQdrant |

---

## 4. Database schema (prompts / agent_states / patches)

PostgreSQL or SQLite tables for mutating prompts and agent memory over time. See blueprint section 4 in OneDrive source for full DDL.

---

## 5. MechIQ (audio + AR)

- Librosa audio diagnosis (belt squeal, engine knock, etc.)
- AutoRepairAdvisor with dynamic SQL patch / `agents_config.json`
- Maps to bleed `auto_repair` in `shared/workflows/bleed-manifest.yaml`

---

## 6. Base44 SDK rules

| Area | Correct API |
|------|-------------|
| Auth | `loginViaEmailPassword`, `me()` — NOT `signIn()` |
| Functions | `functions.invoke('name', data)` — NOT `call()` |
| Entities | `entities.Task.filter`, `get`, `create`, `delete`, `subscribe` |
| Backend admin | `base44.asServiceRole.entities...` in Deno functions |

---

## 7. Vellorae.org landing

Static Tailwind `index.html` — deploy via Cloudflare Pages or Netlify. Full HTML in OneDrive blueprint; also in `docs/business-plan/vellorae-structure.txt`.

---

## 8. Cursor DevOps workflow (“Little Cuttler Protocol”)

1. **Dockerize & test** — missing Dockerfiles for reasoning_agent, memory_agent, agent_claw; `docker compose up --build`
2. **deploy.sh** — build, tag, push Docker Hub, Render/Railway CLI hints
3. **VSIX** — debug → `localhost:8002`, release → `https://api.vellorae.org`

---

## Related repo docs

| Doc | Purpose |
|-----|---------|
| [BUILD_STATUS.md](BUILD_STATUS.md) | What’s built vs blueprint |
| [AGENTS.md](../AGENTS.md) | Cursor memory — 4 projects, commands, bleed map |
| [SOUL.md](../SOUL.md) | Hermes agent identity |
| [docs/agent-stack-specs/INDEX.md](agent-stack-specs/INDEX.md) | 31 merge specs from chat exports |
