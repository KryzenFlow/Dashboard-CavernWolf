# Dashboard CavernWolf — Hermes Studio (Claw Opus)

Hermes is the orchestrator. **Claw Opus is the only agent.** There is no mock agent, no fake replies, and no placeholder secrets.

## Rules

- Fail closed. Missing Merkle root, HMAC key, or OpenClaw gateway → refuse to start or halt.
- Parent (dashboard session) asks Hermes to orchestrate. Children cannot call Claw.
- Claw Opus authenticates against the live Merkle root. Tamper or missing control → alert and terminate the docked Claw daemon.
- **Terminate after each use.** Cycle memory is wiped so Claw keeps listening.
- **Rebuild every day** (UTC hour `CLAW_DAILY_REBUILD_HOUR_UTC`, default 04:00): new Merkle genesis, empty ledger/memory, Claw process restart.
- Backend is **Tailscale-only**. Compose does not publish port 8000 on the host.

## Required environment

Copy `.env.example` and set real values. `dev-change-me`, `mock`, and empty secrets are rejected.

| Variable | Purpose |
|---|---|
| `HERMES_SUPERVISOR_HMAC_KEY` | Signs lifecycle tokens and the Merkle control root |
| `OPENCLAW_GATEWAY_URL` | Real OpenClaw gateway (Claw will not echo) |
| `TS_AUTHKEY` | Optional. Without it, Hermes stays on the docker network only |

## Run

```bash
cp .env.example .env
# fill real keys, then:
docker compose up --build
```

Hermes: internal `8000` (Tailscale Serve on 443)  
Claw Opus: internal `9000` (no host ports)

Local UI without Tailscale: `cd frontend && npm run dev` and point `HERMES_API_BASE` at the Hermes address you actually have. Do not invent a mock backend.

## Layout

```
frontend/     Studio UI (also served by Hermes)
backend/      Hermes orchestrator + gates + Merkle control
claw/         Claw Opus daemon (halt-after-use)
tailscale/    Serve config for the backend
```
