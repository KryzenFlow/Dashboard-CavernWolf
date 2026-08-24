# DOCTOR.md — System State & Integration Blueprint

How this workspace stays lean, secret-free on disk, and fail-closed.
Hermes orchestrates. **Claw Opus is the only agent.** Local Ollama (if used
at all) is guarded by `Doberman.ps1` for IDE/local reasoning — it is not a
mock stand-in for Claw.

## 1. CONTEXT MANAGEMENT (MCP)

- **Static Web MCP:** Prefer a static web MCP protocol to reduce context
  bloat in the Cursor IDE.
- **Amnesia Protocol (`doctor_amnesia.md`):** Agents forget intermediate
  steps once a task is completed and logged. Matches terminate-after-use
  and cycle memory wipe so Claw keeps listening.
- **File Routing:** Large research dumps and file outputs should go to
  Google Drive via MCP when that connector is available — do not stack
  dumps under `$HERMES_HOME/memory` or the repo root.

## 2. SECRETS & TOOL PROVISIONING (Bitwarden Workflow)

- **No local `.env` files for production secrets.**
- Bitwarden holds API keys, tokens, and environment variables.
- The WSL2 FastAPI entry (`wsl_backend/main.py`) authenticates with the
  Bitwarden CLI and pulls secrets at **startup** — it does not load a
  local `.env` for secrets.
- Bitwarden "hands out" tool/API permissions by which vault items are
  fetched for the Hermes Studio role (HMAC key, OpenClaw gateway URL/token,
  Tailscale auth key). Agents never receive long-lived secrets in chat.
- Non-secret layout vars (e.g. `CLAW_URL=http://claw-opus:9000`) may be
  set in compose. Secrets must come from Bitwarden or an already-injected
  process environment after a `bw` unlock on the host.

Required vault item names (password fields unless noted):

| Env var | Bitwarden item name |
|---------|---------------------|
| `HERMES_SUPERVISOR_HMAC_KEY` | `hermes-supervisor-hmac` |
| `OPENCLAW_GATEWAY_URL` | `openclaw-gateway-url` |
| `OPENCLAW_GATEWAY_TOKEN` | `openclaw-gateway-token` |
| `TS_AUTHKEY` | `tailscale-authkey` |

`BW_SESSION` must exist before start (`bw unlock` / `bw login`).

## 3. LOCAL LLM GUARD (Doberman Wrapper)

- **Python Doberman** (`backend/web_gateway/security/doberman_hook_ai.py`):
  deterministic pre-exec gate on Hermes (no model). Fail-closed.
- **Wrapper Script** (`Doberman.ps1`): PowerShell guard for **optional**
  local Ollama calls (Studio/IDE local reasoning only).
- Intercepts requests to local Ollama, validates payload, applies a simple
  rate limit, calls the API, emits **redacted** telemetry for a status bar.
- Never log tokens, `BW_SESSION`, HMAC keys, or Authorization headers.
- Claw Opus still uses `OPENCLAW_GATEWAY_URL` only — not Ollama.

## 4. SECURITY VALIDATION (DeepSeek Architect)

Before merging Bitwarden or Doberman changes:

- Confirm no secret values appear in telemetry JSON or ledger previews.
- Confirm subprocess calls use argument lists (`shell=True` forbidden).
- Confirm Claw halt path never targets the host Docker daemon.
- Confirm Merkle root is required for Claw; missing root → alert + halt.

## 5. How to use this with Cursor

1. Unlock Bitwarden: `export BW_SESSION=$(bw unlock --raw)`.
2. From WSL: `cd` to the repo, `PYTHONPATH=backend python3 -m wsl_backend.main`
   (or `python3 wsl_backend/main.py` with `PYTHONPATH` set).
3. For local Ollama IDE tasks only: run `pwsh ./Doberman.ps1 -Prompt "…"`.
4. Follow `.cursorrules`, `SOUL.md`, and terminate-after-use / daily rebuild.
