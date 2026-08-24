# CavernWolf / Hermes

Control plane for Claw Opus: a FastAPI orchestrator, a docked Claw worker,
a Doberman + Merkle tamper-evident ledger, and a static Studio UI. Hermes
orchestrates. **Claw Opus is the only agent.** There is no mock fallback
and no false environment.

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
- **Studio UI** (`frontend/`) — static HTML/CSS/JS, also served by Hermes.
- **Tailscale** (`tailscale/`) — backend ingress. Compose does not publish
  Hermes or Claw on host ports.
- **Clinic** (`clinic/`) — BAA checklist + CockroachDB sandbox schemas
  (separate compose file, synthetic data only).

## Quick start

```bash
cp .env.example .env
# set real values — empty / mock / dev-change-me secrets refuse to start
docker compose up --build
```

| Service    | Where it listens                         |
|------------|------------------------------------------|
| Hermes     | internal `:8000` (Tailscale Serve `:443`) |
| Claw Opus  | internal `:9000` (no host ports)          |
| Studio     | served by Hermes on the same origin       |

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
(`DOCTOR.md`). Compose may still inject already-resolved secrets from the
host after a Bitwarden unlock; it must not rely on placeholder defaults.

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
backend/      FastAPI orchestrator, gates, Merkle control, JSONL ledger
wsl_backend/  WSL entry — Bitwarden CLI secret pull at startup
claw/         Claw Opus daemon (halt-after-use, real gateway only)
frontend/     Studio UI
tailscale/    Serve config for Hermes
clinic/       BAA + Cockroach sandbox (not on the default compose)
Doberman.ps1  Optional local Ollama guard + redacted telemetry
source/       Notes on original Copilot exports
```

```
backend/web_gateway/app.py                 WS + parent session + Claw dispatch
backend/web_gateway/entry.py               Boot guard (+ optional BW_SESSION pull)
wsl_backend/main.py                        WSL FastAPI entry (Bitwarden required path)
wsl_backend/bitwarden.py                   bw CLI helper (no shell=True)
backend/web_gateway/security/              Token, gates, Merkle, Doberman, cycle
backend/routes/api.py                      Files / skills / git status / control
backend/tests/test_merkle_auth.py          Merkle inclusion + child attenuation
claw/server.py                              Chat proxy + halt-after-use
```

## Status

This tree is the v1 dashboard with Claw Opus wired as the only worker.
Security layers that are implemented: HMAC lifecycle tokens, Merkle root
auth, path confinement, Doberman pre-exec, dual watchers, terminate-after-use,
daily rebuild, Tailscale-only backend, no mock agent.

Not in this repository (do not expect them on `docker compose up`): Tauri
Studio, Ignite precache, MCP server, Ollama/OpenAI/Anthropic/Groq router,
Docker-in-Docker worker pool, STM/LTM stores. Those belong to other
stacks; this README only describes what this repo runs.

## Cursor

Repository system prompt: [`.cursorrules`](.cursorrules). Follow it in this
tree. Do not scaffold Ollama, LangGraph, or numbered `01_` agent packages.

## Further Reading

- [`examples.md`](examples.md) — Practical code examples for tools, hooks, events, and complete extensions
- [`agent-author.md`](agent-author.md) — Step-by-step workflow for agents authoring extensions programmatically
- [`SOUL.md`](SOUL.md) — Claw Opus values, voice, and bright lines
- [`DOCTOR.md`](DOCTOR.md) — System state, Bitwarden, Doberman, amnesia
- [`doctor_amnesia.md`](doctor_amnesia.md) — Forget intermediate steps after log
