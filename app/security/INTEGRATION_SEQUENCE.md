# Supervisor Integration Sequence

Refined fail-closed control flow for Cavern Wolf v2. Implements soul.md / CI.md:
deterministic gates before any model or child; supervisor grants capabilities; watchers
can revoke independently; secrets via Bitwarden at last moment; Merkle integrity.

## Hierarchy (non-negotiable)

```
Supervisor gates  ←  Parent only (host tier)
       ↑
    Parent          ←  talks to supervisor, spawns children
       ↑ ask_parent (never supervisor)
    Child           ←  always execution_tier=container, behind parent
```

| Rule | Enforcement |
|------|-------------|
| Children ask **parent**, never supervisor | `handle_agent_request()` BLOCKs child tokens |
| Children run in **containers** behind parent | `execution_tier=container` on child tokens |
| Only **parent** may spawn children | `issue_child_token()` rejects child issuers |
| Child upward channel | `ask_parent` capability only |
| Parent talks to supervisor | `execution_tier=host`, role=parent |

Child requests use `handle_child_via_parent()` — parent decides if supervisor is needed.

## Visual flow

```
Payload
  │
  ├─ 1. Lifecycle token + capability check     → BLOCK (+ scoped revoke if severe)
  ├─ 2. path_confinement.check_payload()       → BLOCK (request rejected only)
  ├─ 3. doberman_hook.pre_exec()               → BLOCK (request rejected only)
  │
  └─ PASS
       │
       ▼
Supervisor decides (allow / child / escalate)
       │
       ├─ issue_child_token (strict subset caps)
       │     │
       │     ├─ Dual watchers (scoped revoke — child agent only)
       │     └─ Child runs in container — short-lived
       │
       └─ decision_ledger (HMAC) + merkle_auth batch root
```

## Blast-radius policy

Revocation is scoped to the minimum affected agent(s). Most BLOCKs reject the request only.

| Scope | When | Effect |
|-------|------|--------|
| **NONE** | Path confinement, Doberman, capability denied, child issuance errors | Request rejected; parent and siblings stay alive |
| **AGENT** | Child contacts supervisor, child policy violation | `revoke_agent(child_id)` — parent unaffected |
| **TREE** | Invalid signature, Merkle tamper, stale/forged root | `revoke_tree(tree_id)` — entire session killed |

Watchers follow the same rule: child watchers call `revoke_agent`; parent watchers call `revoke_tree`.

## Module map

| Module | Role |
|--------|------|
| `integration.py` | `handle_agent_request()` entry point |
| `supervisor_gates.py` | `validate_and_gate()` — Steps A–C |
| `token.py` | `issue_token`, `issue_child_token`, `revoke_agent`, `revoke_tree` |
| `revocation_policy.py` | `classify_block()` — NONE / AGENT / TREE scope |
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
4. **Watcher kill** — scoped revoke (`revoke_agent` for children, `revoke_tree` for severe parent signals) without supervisor consensus
5. **Merkle batching** — `HERMES_LEDGER_BATCH_SIZE` (default 50) or `HERMES_MERKLE_BATCH_SECONDS` (10)

## Bitwarden

Long-lived secrets never enter child containers. Fetch at startup via Bitwarden gateway;
wipe on cycle death (see `infra/secure-agent/agent_runner.sh`).
