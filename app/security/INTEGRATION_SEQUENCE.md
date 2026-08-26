# Supervisor Integration Sequence

Refined fail-closed control flow for Cavern Wolf v2. Implements soul.md / CI.md:
deterministic gates before any model or child; supervisor grants capabilities; watchers
can revoke independently; secrets via Bitwarden at last moment; Merkle integrity.

## Visual flow

```
Payload
  │
  ├─ 1. Lifecycle token + capability check     → BLOCK + revoke_tree
  ├─ 2. path_confinement.check_payload()       → BLOCK
  ├─ 3. doberman_hook.pre_exec()               → BLOCK
  │
  └─ PASS
       │
       ▼
Supervisor decides (allow / child / escalate)
       │
       ├─ issue_child_token (strict subset caps)
       │     │
       │     ├─ Dual watchers (independent revoke)
       │     └─ Child runs in container — short-lived
       │
       └─ decision_ledger (HMAC) + merkle_auth batch root
```

## Module map

| Module | Role |
|--------|------|
| `integration.py` | `handle_agent_request()` entry point |
| `supervisor_gates.py` | `validate_and_gate()` — Steps A–C |
| `token.py` | `issue_token`, `issue_child_token`, `revoke_tree` |
| `path_confinement.py` | Path / traversal / destructive cmd gate |
| `doberman_hook.py` | Deterministic pre-exec (no model) |
| `control_plane.py` | Live Merkle leaves for tokens + decisions |
| `decision_ledger.py` | HMAC JSONL + batch Merkle roots |
| `merkle_auth.py` | Auth Merkle tree (distinct from audit `merkle.py`) |
| `merkle.py` | Session AuditLedger (SQL seal) |
| `watchers.py` | Dual independent revoke watchers |

## Usage

```python
import os
os.environ["HERMES_SUPERVISOR_HMAC_KEY"] = "..."  # from Bitwarden at runtime

from app.security.integration import bootstrap_supervisor_session, handle_agent_request

parent = bootstrap_supervisor_session(
    ["read_workspace", "run_static_scan"],
    ttl_seconds=300,
)

payload = {
    "action": "run_static_scan",
    "agent_id": parent["agent_id"],
    "session_id": parent["tree_id"],
    "path": "backend/routes/api.py",
}

result = handle_agent_request(
    payload,
    parent,
    child_capabilities=["run_static_scan"],
    child_ttl=90,
)

if result.verdict != "PASS":
    raise SystemExit(result.reason)

# result.child_token → pass to ephemeral container only
# result.watchers.stop() when child completes
```

## Invariants

1. **Capability attenuation** — `child_capabilities ⊆ parent_capabilities`
2. **Fail-closed** — any gate exception → BLOCK
3. **No model in gates** — Steps A–C are pure policy
4. **Watcher kill** — `revoke_tree()` without supervisor consensus
5. **Merkle batching** — `HERMES_LEDGER_BATCH_SIZE` (default 50) or `HERMES_MERKLE_BATCH_SECONDS` (10)

## Bitwarden

Long-lived secrets never enter child containers. Fetch at startup via Bitwarden gateway;
wipe on cycle death (see `infra/secure-agent/agent_runner.sh`).
