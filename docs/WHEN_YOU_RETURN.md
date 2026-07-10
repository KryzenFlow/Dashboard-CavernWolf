# When you return — action checklist

Created while you were away. Work through in order.

---

## Part A: Vellorae.org + Namecheap + Cloudflare DNS

Your domain is at **Namecheap**. Hosting the site on **Cloudflare Pages** is the right path. You do **not** need to guess A vs CNAME — Cloudflare tells you exactly what to add after you connect the domain.

### Step 1 — Add domain to Cloudflare (if not done)

1. Log in: [https://dash.cloudflare.com](https://dash.cloudflare.com)
2. **Add a site** → enter `vellorae.org`
3. Pick the **Free** plan
4. Cloudflare scans existing DNS — you can skip/import
5. Cloudflare shows **two nameservers** (e.g. `ada.ns.cloudflare.com` and `bob.ns.cloudflare.com`)

### Step 2 — Point Namecheap to Cloudflare

1. Log in: [https://www.namecheap.com](https://www.namecheap.com) → Domain List → **vellorae.org** → **Manage**
2. **Nameservers** → change from "Namecheap BasicDNS" to **Custom DNS**
3. Paste the **two Cloudflare nameservers** from Step 1
4. Save — propagation can take **15 minutes to 48 hours** (often under 1 hour)

You do **not** set A/CNAME at Namecheap once nameservers point to Cloudflare. All DNS is managed in Cloudflare after that.

### Step 3 — Deploy the landing site to Cloudflare Pages

Site files are already in the repo:

```
E:\Dashboard-CavernWolf\shared\workflows\vellorae-demos\
  index.html          ← umbrella / clinic landing
  elite-wellness/     ← demo clinic MVP
```

**Option A — Dashboard (easiest first time)**

1. Cloudflare → **Workers & Pages** → **Create** → **Pages** → **Upload assets**
2. Project name: `vellorae-main` (matches existing wrangler cache)
3. Upload the folder `vellorae-demos` (or zip it first)
4. Deploy

**Option B — Wrangler CLI (from repo)**

```powershell
cd E:\Dashboard-CavernWolf
npm install -g wrangler
wrangler login
wrangler pages deploy shared/workflows/vellorae-demos --project-name=vellorae-main
```

`wrangler.toml` is now in the repo root.

### Step 4 — Attach custom domain in Cloudflare Pages

1. Pages → **vellorae-main** → **Custom domains**
2. Add `vellorae.org`
3. Add `www.vellorae.org` (optional but recommended)
4. Cloudflare auto-creates DNS records in your zone — usually:
   - `vellorae.org` → CNAME to `vellorae-main.pages.dev` (or proxied A/flattened)
   - `www` → CNAME to `vellorae-main.pages.dev`
5. Wait for **Active** status + SSL certificate (usually minutes)

### Step 5 — Verify

- [ ] https://vellorae.org loads the landing page
- [ ] https://www.vellorae.org redirects or loads (if added)
- [ ] SSL padlock shows valid certificate

### Future subdomains (from blueprint)

| Subdomain | Purpose | When |
|-----------|---------|------|
| `demo.vellorae.org` | HTMX/HTML demos | Second Pages project or path |
| `vip.vellorae.org` | VIP webhooks / alerts | After agent stack deploy |
| `api.vellorae.org` | Hermes / Agent Claw API | Railway/Render + CF proxy |

---

## Part B: Dashboard CavernWolf — get it working locally

### What was fixed while you were away

- **Ops dashboard JS bug** — `ops_dashboard/script.js` had a syntax error (`}))` → `})`) that broke **all buttons**
- **`.env.example`** — now includes CORS for port 3001 and defaults `STUDIO_MODE=internal` for private ops
- **`wrangler.toml`** — added for Cloudflare Pages
- **`cloudflare-pages`** deploy profile added to `deploy-profiles.yaml`
- **`.wrangler/`** added to `.gitignore` (account cache should not be committed)

### Your steps

```powershell
cd E:\Dashboard-CavernWolf

# 1. Sync env (if .env is old or missing)
copy .env.example .env
# Edit .env: confirm STUDIO_MODE=internal for ops dashboard

# 2. Start minimal stack (safe, no AI token burn)
.\scripts\start_minimal.ps1

# 3. Verify health
.\scripts\verify_stack.ps1

# 4. Optional: OneDrive-backed memory DBs
.\scripts\setup_onedrive_data.ps1

# 5. Open UIs
# Hermes Studio (customer):  http://localhost:3000
# Agent Ops (private):       http://localhost:3001
# Backend API:               http://localhost:8000/health
```

### "Settings button doesn't work"

| What you might mean | Reality | Fix |
|---------------------|---------|-----|
| Base44 prototype Settings | **Not in this repo** — external app | Audit Base44 separately (Part C) |
| Hermes Studio ⚙️ icon | **Decorative only** — not a button yet | AgentHub Settings UI is in docs backlog |
| Ops dashboard buttons dead | Was JS syntax error + `STUDIO_MODE=public` | Fixed JS; set `STUDIO_MODE=internal` |

For full stack with UI:

```powershell
docker compose up --build
```

---

## Part C: Base44 prototype — privacy before you migrate

**Base44 code is NOT in Dashboard-CavernWolf.** Your prototype lives on Base44's platform. Do not import YAML or entities until you audit it.

### Checklist before trusting Base44 data in Hermes

- [ ] List what **entities** exist in Base44 (users, clinics, PHI, API keys in fields?)
- [ ] Is the Base44 app URL **public** or login-gated?
- [ ] Export entity schemas — any emails, phone numbers, patient data?
- [ ] Rotate any API keys that were stored in Base44 entity fields
- [ ] Decide: **demo-only** (rebuild fresh in Hermes) vs **migrate** (map entities → SQLite)

### Hermes is safer for clinic pilots because

- `STUDIO_MODE=public` blocks agent stack API and token-bearing CLI on customer-facing studio
- `studio_security.py` enforces command allowlists
- PHI paths are in `.gitignore`
- `clinic/compliance/BAA_CHECKLIST.md` exists for HIPAA planning

### Base44 → Hermes mapping (when ready)

| Base44 | Hermes |
|--------|--------|
| `functions.invoke` | `POST /action`, Agent Claw `/execute` |
| `entities.*` | SQLite (`data/*.db`), Chroma, Redis |
| `loginViaEmailPassword` | Your auth layer + `STUDIO_MODE=internal` for ops |
| Settings UI | Build in `frontend/` or ops_dashboard (spec in `docs/agent-stack-specs/`) |

**Recommendation:** Treat Base44 as a **UI prototype only**. Rebuild settings and entities in Hermes rather than piping Base44 YAML into docker-compose.

---

## Part D: Cloud agent stack (your idea)

### What's already built

| Component | Location | Status |
|-----------|----------|--------|
| 8-agent registry | `shared/agents/registry.yaml` | ✅ |
| Orchestration pipeline | `backend/agents/orchestration/` | 🟡 Partial |
| Memory (SQLite + Chroma + Redis) | `backend/agents/memory/` | ✅ |
| Agent Claw execution | `agent_claw/` | ✅ |
| Ops API | `backend/routes/ops.py` | ✅ (needs `STUDIO_MODE=internal`) |
| Worker auto-run | `scripts/agent_worker.ps1` | ✅ |

### Env flags (in `.env`)

```
AGENT_STACK_ENABLED=1       # Route through orchestration
AGENT_STACK_USE_AI=0        # Keep 0 until you want token spend; set 1 for full AI
STUDIO_MODE=internal        # Required for ops dashboard + agent APIs
ACTIVE_BLEED=vellorae       # Switch vertical without code changes
```

### What's still blueprint-only

- VersionEvaluator, Auto-Debugger, Ghost Scraper
- Qdrant (using Chroma today)
- CockroachDB production (sandbox profile exists)
- LangGraph SqliteSaver supervisor
- VIP webhooks → `vip.vellorae.org`
- AgentHub Settings UI (31 specs in `docs/agent-stack-specs/`)

### Suggested cloud deploy path (when local stack is green)

1. **vellorae.org** → Cloudflare Pages (static landing) — Part A
2. **api.vellorae.org** → Railway or Render (backend + agent-claw) — add later
3. **Redis/Chroma** → managed services or keep local until scale needs it
4. **vip.vellorae.org** → CF Worker for webhook receiver

---

## Part E: OneDrive workspace cleanup (when you have time)

Path: `C:\Users\BossMan\OneDrive\Desktop\New Project Workspace`

| Folder | Action |
|--------|--------|
| `.VELLORAE_MASTER_BLUEPRINT.md.txt` | Archived in repo → `docs/VELLORAE_MASTER_BLUEPRINT.md` |
| `Greese Mokey Auto Repair AI` | Keep; don't copy into repo (80k+ files) |
| `Data for Dashboard…` | Run `.\scripts\sync_desktop_reference.ps1` |
| `2nd Dashboard` | Archive chat exports |

---

## Quick reference — key files

| File | Purpose |
|------|---------|
| [AGENTS.md](../AGENTS.md) | Cursor memory — 4 projects |
| [BUILD_STATUS.md](BUILD_STATUS.md) | Built vs missing |
| [VELLORAE_MASTER_BLUEPRINT.md](VELLORAE_MASTER_BLUEPRINT.md) | Master vision |
| [wrangler.toml](../wrangler.toml) | Cloudflare Pages config |
| `shared/workflows/vellorae-demos/` | Site to deploy |
| `.env` | **You** must set `STUDIO_MODE=internal` for ops |

---

## Priority order when you sit down

1. ☐ Namecheap nameservers → Cloudflare (Part A steps 1–2)
2. ☐ Deploy `vellorae-demos` to Cloudflare Pages (Part A step 3)
3. ☐ Attach `vellorae.org` custom domain (Part A step 4)
4. ☐ `copy .env.example .env` + start stack + `verify_stack.ps1` (Part B)
5. ☐ Open http://localhost:3001 — confirm ops dashboard connects
6. ☐ Audit Base44 prototype privacy before any migration (Part C)
7. ☐ Set `ACTIVE_BLEED=vellorae` when building clinic pilots (Part D)

---

*Questions when you're back: tell me which step you're on and I'll walk through it live.*
