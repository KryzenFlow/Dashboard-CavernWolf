# Getting started — one page, no overwhelm

You have **one main repo** (`E:\Dashboard-CavernWolf`) and **three brands**. Everything else is notes, prototypes, or sandboxes until we merge the good parts.

---

## Your three brands (simple map)

| Brand | Domain | What it does | Where code lives |
|-------|--------|--------------|------------------|
| **CavernWolf / Hermes** | (local dashboard) | Agent Hub, Docker stack, build sites, orchestrate tools | `E:\Dashboard-CavernWolf` |
| **Vellorae.org** | vellorae.org | Agency umbrella — clinic pilots, better workflows for independent doctors | `shared/workflows/vellorae-demos/` + bleed `vellorae` |
| **LocalRankai.net** | localrankai.net | Auto repair guide + local SEO tools | OneDrive `Greese Mokey Auto Repair AI\` (merge later) |

**HIPAA rule for clinics:** Agents handle **marketing, booking, SMS, calendar** — they do **not** store patient charts. Existing clinic software keeps PHI. That keeps BAA scope small. See `clinic/compliance/BAA_CHECKLIST.md`.

---

## Base44 prototype vs real dashboard

Your **Clawboard / CavernWolf Studio v0.1** screenshots (Base44) are a **UI prototype**. The repo is the **real engine**.

| Base44 has | Repo has today | Gap |
|------------|----------------|-----|
| Agent Hub + New Agent wizard | `shared/agents/registry.yaml` (8 agents, YAML only) | Need React AgentHub UI |
| Scorecard / health check | `scripts/verify_stack.ps1` | Need in-dashboard Scorecard page |
| Tools & hooks picker | Agent Claw tools | Need wizard UI wired to API |
| GrokAdapter, Qdrant agents | Registry + docs | Qdrant not in compose (Chroma instead) |
| Settings gear | Not wired | Build settings panel |

**Do not migrate Base44 config into Docker.** Copy the **look and workflows** into Hermes. Keep patient/marketing data out of Base44.

Your Scorecard screenshot showed everything **offline** because Docker wasn't running — not because the design is wrong.

---

## Azure-style sandbox (your idea)

```
Production (Vellorae / LocalRank live sites)
    └── Cloudflare Pages, real domains

Sandbox (test agents, demos, patches)
    └── docker-compose.minimal.yml  OR  clinic/docker-compose.sandbox.yml
    └── mock data only, no real PHI
    └── ACTIVE_BLEED switches vertical without code edits
```

**Today:** `docker compose -f docker-compose.minimal.yml up` = sandbox.  
**Later:** separate Cloudflare Pages project `sandbox.vellorae.org` for demos.

---

## How to give Cursor your USB files

Your USB is **G:\** (label: Good2Go USB). Cursor can already read it when it's plugged in.

**Easiest (recommended):**

```powershell
cd E:\Dashboard-CavernWolf
.\scripts\ingest_usb_notes.ps1
```

That copies all `.txt` / `.md` / `.pdf` from `G:\` into `docs\inbox\usb-good2go\`. Then say in chat:

> "Review docs/inbox/usb-good2go and pick the best ideas for the dashboard."

**Other options:**

1. **Open USB in Cursor** — File → Open Folder → `G:\`
2. **Copy manually** — drag folders into `E:\Dashboard-CavernWolf\docs\inbox\`
3. **OneDrive** — already at `Desktop\New Project Workspace` (we've indexed this)

You do **not** need special permissions. If the drive letter is plugged in, I can read it.

---

## Do these 4 things first (today)

### 1. Start Docker Desktop

Make sure Docker Desktop is running (whale icon in system tray).

### 2. Start the stack

```powershell
cd E:\Dashboard-CavernWolf
copy .env.example .env
.\scripts\start_minimal.ps1
.\scripts\verify_stack.ps1
```

When green: backend `:8000`, claw `:9000`. Full UI adds `:3000` and `:3001`.

### 3. Ingest USB notes

```powershell
.\scripts\ingest_usb_notes.ps1
```

### 4. Tell me what you finished

Example: *"Docker is green, USB notes ingested, ready for Agent Hub plan."*

---

## What I will do next (when you're ready)

1. Review USB + OneDrive notes — extract orchestration, harness, AgentHub JSX ideas
2. Map Base44 screens → build list for `frontend/` (Agent Hub, Scorecard, Settings)
3. Wire sandbox compose + bleed switching for clinic vs auto repair
4. Vellorae.org on Cloudflare (see `docs/WHEN_YOU_RETURN.md` Part A)
5. LocalRank auto repair — pick **one** folder from Grease Monkey tree to import

---

## Stop using multiple editors for the same job

| Tool | Use for |
|------|---------|
| **Cursor** | Dashboard-CavernWolf repo — only editor for this project |
| **Base44** | Reference screenshots only — don't deploy new YAML there |
| **Qoder / others** | Archive — run `ingest_usb_notes` or copy exports into `docs/inbox/` |

---

## Key files

- [WHEN_YOU_RETURN.md](WHEN_YOU_RETURN.md) — Cloudflare DNS, Base44 privacy
- [AGENTS.md](../AGENTS.md) — project memory
- [BUILD_STATUS.md](BUILD_STATUS.md) — what's built vs missing
- [VELLORAE_MASTER_BLUEPRINT.md](VELLORAE_MASTER_BLUEPRINT.md) — master vision

---

*One step at a time. Cutler built the highway — you're laying the on-ramps.*
