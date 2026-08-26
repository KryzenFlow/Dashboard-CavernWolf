# CI.md — Context Initialization
> Loaded at session boot alongside SOUL.md. Defines the Cavern Wolf v2 session
> lifecycle, credential injection, and audit sealing. Hermes orchestrates;
> Claw Opus is the only agent that acts.

---

## Session Lifecycle

```
  [IMAGE STORED]  ← Clean, versioned, governance-locked snapshot
       │
       ▼
  BOOT triggered (by you)
       │
       ▼
  Bitwarden injects API keys + credentials at runtime only
  soul.md + CI.md load as root context
  Claude Opus initializes fresh
       │
       ▼
  [ACTIVE SESSION — you are present]
       │
       ▼
  Session ends OR inactivity threshold hit OR you trigger shutdown
       │
       ▼
  AUTOMATIC TERMINATION
    ├── Agent lifecycle CUT — no persistence, no memory bleed
    ├── Bitwarden revokes all injected credentials automatically
    ├── API keys rotate or expire (optional but recommended)
    └── Runtime state wiped — image untouched
       │
       ▼
  [IMAGE STORED]  ← Exactly where you started. Ready when you return.
```

---

## Boot Sequence

1. **Image stored** — Container or VM starts from a clean, versioned snapshot.
   No secrets on disk. No session memory from prior runs.

2. **BOOT triggered (by you)** — Session starts only when you invoke it.
   Implicit auto-start without governance docs loaded is forbidden in production.

3. **Credential inject** — Bitwarden CLI unlocks vault items at runtime only.
   Required secrets never land in repo files, chat, or persistent volume mounts.
   Record `CREDENTIAL_INJECT` in the audit ledger (payload hashed, never stored raw).

4. **Root context load** — Read and apply:
   - `soul.md` / `SOUL.md` — values, voice, fail-closed ethics
   - `CI.md` — this lifecycle and boot contract
   - Optional regional overlays: `CI_[REGION].md` (see SOUL.md)

5. **Claude Opus initializes fresh** — No prior cycle memory. Hermes orchestrates;
   Claw Opus remains gated until token + Merkle membership pass.

6. **Audit session open** — `AuditLedger.new_session(agent="cavern_wolf_v2", previous_root=...)`
   chains Merkle roots across sessions. First entry is always `SESSION_BOOT`.
   Sealed on automatic termination (see Termination & Seal).

---

## Active Session Rules

| Event | Ledger action | Actor |
|-------|---------------|-------|
| Tool invocation | `TOOL_CALL` | agent |
| Model output | `OUTPUT_GENERATED` | agent |
| Escalation / halt | `ESCALATION` | agent |
| Supervisor decision | `SUPERVISOR_DECISION` | system |
| Credential refresh | `CREDENTIAL_INJECT` | system |

- Raw payloads are **never** stored. Only `payload_hash` (SHA-256 of canonical JSON).
- Sequence numbers are monotonic and verified on seal.
- Session cannot accept new entries after `seal()`.

---

## Termination & Seal

Wire `terminate_session()` from `app/security/merkle.py` to `SIGTERM`, `SIGINT`,
and Docker `STOPSIGNAL`:

```python
import signal
import sys

from app.security.merkle import AuditLedger, terminate_session

ledger = AuditLedger.new_session(agent="cavern_wolf_v2")

def shutdown(signum, frame):
    root = terminate_session(ledger, db_insert_fn=my_db_write)
    print(f"[SEALED] {root}")
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)
```

On shutdown:

1. Record `TERMINATION_SIGNAL`
2. Record `SESSION_SEAL` (automatic inside `seal()`)
3. Compute Merkle root over all entry hashes
4. Persist row to `audit_ledger` (SQL Server schema in `merkle.py`)
5. Revoke Bitwarden-injected credentials
6. Wipe runtime memory — image unchanged

---

## Verification

After insert, run verification before marking `verified = 1`:

```python
from app.security.merkle import AuditLedger

if not AuditLedger.verify_sealed_record(sql_row):
    raise Alert("TAMPER DETECTED — audit_ledger row failed Merkle verification")
```

Verification recomputes every entry hash from stored fields and rebuilds the
Merkle root. Tampering with `action`, `actor`, `payload_hash`, sequence, or
root substitution returns `False`.

---

## Fail-Closed Bright Lines

- Never boot without SOUL.md and CI.md in root context.
- Never skip `AuditLedger.new_session()` at boot.
- Never persist raw payloads — hash only.
- Never treat a missing Merkle root as optional for Claw Opus.
- Never leave a session unsealed on termination.
- Never carry cycle memory into the next boot — chain via `previous_root` only.

---

## Related Files

| File | Role |
|------|------|
| `SOUL.md` | Values, voice, cultural rules |
| `app/security/merkle.py` | AuditLedger, Merkle tree, SQL record, shutdown hook |
| `DOCTOR.md` | System integration blueprint (when present) |
| `doctor_amnesia.md` | Amnesia protocol for cycle memory wipe |
