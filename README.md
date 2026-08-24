# CavernWolf / Hermes Studio Dash

Control plane for Claw Opus: a FastAPI orchestrator, a docked Claw worker,
a Doberman + Merkle tamper-evident ledger, and Hermes Studio Dash.
Hermes orchestrates. Specialists on the roster **propose**. **Claw Opus
is the only execution worker.** There is no mock fallback and no false
environment.

Parent sessions ask Hermes. Children do not call Claw. Claw authenticates
against the live Merkle root; missing or forged control alerts and
terminates the docked Claw daemon. After each use the daemon is halted and
cycle memory is wiped. The control plane rebuilds daily.

## Stack

- **Backend** — FastAPI (`backend/web_gateway`), fail-closed gates
  (lifecycle token, path confinement, Doberman hook), HMAC-signed Merkle
  control plane + JSONL ledger. No mock LLM router.
- **Claw Opus** (`claw/`) — docked worker. Talks only to a real OpenClaw
  gateway. Halts after each cycle. 24h max lifetime, then rebuild.
- **Studio UI** (`frontend/` live static; `src/` Tauri/React scaffold) —
  Agent Pull-Down, Agent Delete, System Status Bar.
- **Agent matrix** (`wsl_backend/agents/`) — Hermes, two reasoning, two
  memory, Codex, Grok, DeepSeek Architect, Claw Opus.
- **Tailscale** (`tailscale/`) — backend ingress. WSL Hermes binds the
  Tailscale IPv4. Compose does not publish Hermes or Claw on host ports.
- **Memory compose** (`docker-compose.yml`) — Redis + Qdrant on loopback
  only. Not Claw's brain.
- **Clinic** (`clinic/`) — BAA checklist + CockroachDB sandbox schemas
  (separate compose file, synthetic data only).

## Quick start

Memory backends (localhost only — WSL memory agents):

```bash
# REDIS_PASSWORD from Bitwarden, never a committed placeholder
docker compose up -d
```

Hermes + Claw Opus + Tailscale:

```bash
cp .env.example .env
# set real values — empty / mock / dev-change-me secrets refuse to start
docker compose -f docker-compose.stack.yml up --build
```

| Service    | Where it listens                         |
|------------|------------------------------------------|
| Hermes     | internal `:8000` (Tailscale Serve `:443`) |
| Claw Opus  | internal `:9000` (no host ports)          |
| Studio     | served by Hermes on the same origin       |
| Redis      | `127.0.0.1:6379` (memory compose)         |
| Qdrant     | `127.0.0.1:6333` (memory compose)         |

Local UI without Tailscale:

```bash
cd frontend && npm run dev
```

Point `window.HERMES_API_BASE` at the Hermes address you actually have.
Do not invent a mock backend. Hermes will not start with `HERMES_MOCK=1`.

```bash
cd backend
PYTHONPATH=. HERMES_SUPERVISOR_HMAC_KEY=… CLAW_URL=http://127.0.0.1:9000 \
  python3 -m web_gateway.entry
```

Health: `GET /health` (Merkle root present, agent `claw-opus`).

## Secrets

Secrets are injected at runtime — never committed. Bitwarden is the
vault. **Do not load production secrets from a local `.env`.**

On WSL, unlock then start Hermes:

```bash
export BW_SESSION=$(bw unlock --raw)
PYTHONPATH=backend:. python3 -m wsl_backend.main
```

`wsl_backend` pulls vault items into the process environment at startup
(`DOCTOR.md`) and binds FastAPI to the Tailscale IPv4 (`HERMES_BIND_TAILSCALE=1`).
Set `TS_IP` or join the tailnet first. Compose may still inject already-resolved
secrets from the host after a Bitwarden unlock; it must not rely on placeholder
defaults.

| Variable | Required | Purpose |
|----------|----------|---------|
| `BW_SESSION` | for WSL Bitwarden pull | Session from `bw unlock` |
| `HERMES_SUPERVISOR_HMAC_KEY` | yes | From vault item `hermes-supervisor-hmac` |
| `OPENCLAW_GATEWAY_URL` | yes | From vault item `openclaw-gateway-url` |
| `OPENCLAW_GATEWAY_TOKEN` | if the gateway requires it | From vault item `openclaw-gateway-token` |
| `TS_AUTHKEY` | no | From vault item `tailscale-authkey` |
| `CLAW_DAILY_REBUILD_HOUR_UTC` | no | Daily genesis + memory wipe (default `4`) |

There is no default HMAC key and no `LEDGER_KEY:-supersecretkey` fallback.
Placeholder values (`mock`, `dev-change-me`, empty) are rejected at boot.

## Project layout

```
.cursorrules     Hermes Studio Dash system prompt (no Ollama/LangGraph v2)
src/             Studio Dash React/TS (Agent Pull-Down, Delete, Status Bar)
src-tauri/       (optional) Tauri shell target
wsl_backend/     WSL FastAPI — Bitwarden, Tailscale bind, agent matrix
  agents/        Hermes, reasoning x2, memory x2, Codex, Grok, DeepSeek, Claw
  memory/        Redis + vector connectors (fail closed if unset)
  tools/         bash arg-lists, REST CLI, plugins
backend/         gates, Merkle, Claw client, FastAPI orchestrator
claw/            Claw Opus daemon (halt-after-use, real gateway only)
frontend/        live static Studio (served by Hermes)
plugins/         Agent Builder plugin manifests
docker-compose.yml         Redis + Qdrant (loopback)
docker-compose.stack.yml   Hermes + Claw + Tailscale
tailscale/       Serve config for Hermes
```

backend/web_gateway/app.py                 WS + parent session + Claw dispatch + /agents
backend/web_gateway/entry.py               Boot guard (+ optional BW_SESSION pull)
wsl_backend/main.py                        WSL FastAPI entry (Tailscale bind)
wsl_backend/agents/                        Dynamic roster base classes
wsl_backend/routes_agents.py               GET/POST/DELETE /agents, /system/status
wsl_backend/tailscale_net.py               Detect Tailscale IPv4 (arg-list, no shell)
wsl_backend/bitwarden.py                   bw CLI helper (no shell=True)
backend/web_gateway/security/              Token, gates, Merkle, Doberman, cycle
backend/routes/api.py                      Files / skills / git status / control
backend/tests/test_agent_matrix.py         Roster + Tailscale + HTTP /agents
backend/tests/test_merkle_auth.py          Merkle inclusion + child attenuation
claw/server.py                              Chat proxy + halt-after-use
src/components/AgentPullDown.tsx            Agent selector
src/components/AgentDelete.tsx              Delete instance
src/components/SystemStatusBar.tsx          Bottom status bar
```

## Status

This tree is the v1 dashboard with a dynamic agent roster and Claw Opus as
the only execution worker. Security layers that are implemented: HMAC
lifecycle tokens, Merkle root auth, path confinement, Doberman pre-exec,
dual watchers, terminate-after-use, daily rebuild, Tailscale-only backend,
no mock agent.

`src/` is the Hermes Studio Dash scaffold (pull-down, delete, status bar).
The live Studio remains `frontend/` until the Tauri shell is packaged.
Do not expect Ollama, LangGraph, or numbered `01_` agent folders.

## Cursor

Repository system prompt: [`.cursorrules`](.cursorrules). Follow it in this
tree. Do not scaffold Ollama, LangGraph, or numbered `01_` agent packages.

## Further Reading

- [`examples.md`](examples.md) — Practical code examples for tools, hooks, events, and complete extensions
- [`agent-author.md`](agent-author.md) — Step-by-step workflow for agents authoring extensions programmatically
- [`SOUL.md`](SOUL.md) — Claw Opus values, voice, and bright lines
- [`DOCTOR.md`](DOCTOR.md) — System state, Bitwarden, Doberman, amnesia
- [`doctor_amnesia.md`](doctor_amnesia.md) — Forget intermediate steps after log
