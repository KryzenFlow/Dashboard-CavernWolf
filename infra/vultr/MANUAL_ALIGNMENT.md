# Vultr API Manual Alignment

This module implements **Vultr API Reference v1.0 (2020-09-11)** — the manual you provided.
All endpoints, auth, and HTTP semantics match that document.

**Source of truth:** `source/vultr-api-reference-v1.pdf`

## Authentication (Manual — Overview)

| Manual | Implementation |
|--------|----------------|
| `https://api.vultr.com/` | `infra/vultr/constants.py` → `API_BASE` |
| Header `API-Key: YOURKEY` | `VultrClient` sets `API-Key` on authenticated requests |
| Key from my.vultr.com settings | Env var `VULTR_API_KEY` (never commit) |

## HTTP response codes (Manual — Overview)

| Code | Meaning | `VultrAPIError` |
|------|---------|-----------------|
| 200 | Success | — |
| 400 | Invalid URL | raised |
| 403 | Invalid/missing API key | raised |
| 405 | Wrong HTTP method | raised |
| 412 | Request failed | raised |
| 500 | Server error | raised |
| 503 | Rate limit (~2/s) | raised; client throttles to 0.55s between calls |

## CI.md lifecycle ↔ Vultr API

| CI.md stage | Vultr API v1 (manual) | Code |
|-------------|----------------------|------|
| **[IMAGE STORED]** | `GET /v1/snapshot/list` | `VultrClient.snapshot_list()` |
| **BOOT triggered** | `POST /v1/server/create` with `OSID=164` + `SNAPSHOTID` | `server_create_from_snapshot()` |
| **Bitwarden inject** | (on VM after SSH — not Vultr API) | `agent_runner.sh` + `BW_SESSION` |
| **soul.md + CI.md load** | Startup script optional: `SCRIPTID` on create | `startupscript_create()` |
| **[ACTIVE SESSION]** | Poll until `status=active`, `server_state=ok` | `wait_server_active()` |
| **AUTOMATIC TERMINATION** | `POST /v1/server/halt` then `POST /v1/server/restore_snapshot` to **baseline** | `terminate_and_seal()` |
| **[IMAGE STORED] seal** | Record clean `SNAPSHOTID` — **do not** `snapshot/create` on session disk | `ConfigurationRecord.sealed_from_baseline` |
| **Rollback** | `POST /v1/server/restore_snapshot` | `server_restore_snapshot()` / `VultrSessionLifecycle.rollback()` |

Manual quote (server/create):

> In order to create a server using a snapshot, use **OSID 164** and specify a **SNAPSHOTID**.

## Infrastructure Hub data model ↔ manual

| Hub model | Vultr manual |
|-----------|--------------|
| `Environments` | Account + `DCID` (regions/list) + `FIREWALLGROUPID` |
| `VMInstances` | `SUBID` from server/create; fields from server/list |
| `Configurations` | `SNAPSHOTID` chain + `ConfigurationRecord.parent_config_id` |
| `ResourceLogs` | `GET /v1/server/bandwidth?SUBID=` |

## Firewall (Manual — Firewall section)

SSH-only access pattern for secure agents:

1. `POST /v1/firewall/group_create`
2. `POST /v1/firewall/rule_create` — allow TCP 22 from your IP (`subnet` + `subnet_size`)
3. `POST /v1/server/create` with `FIREWALLGROUPID=...` **or** `server_firewall_group_set`

Do not expose agent/Docker ports in Vultr firewall — container iptables allowlist handles outbound.

## Secure agent on Vultr

After `boot_from_snapshot()` and `wait_server_active()`:

```bash
ssh root@MAIN_IP
export BW_SESSION=$(bw unlock --raw)
cd /opt/cavernwolf/infra/secure-agent && ./agent_runner.sh
```

Register bootstrap once via manual `POST /v1/startupscript/create` (contents of `vultr_bootstrap.sh`).

## Audit ledger integration

Every lifecycle transition should call `AuditLedger.record()` with hashed payloads:

| Action | Ledger action |
|--------|---------------|
| Boot from snapshot | `VULTR_BOOT` |
| Halt + snapshot seal | `VULTR_SEAL` |
| Restore snapshot | `VULTR_ROLLBACK` |

Chain `previous_root` (Merkle) alongside `ConfigurationRecord.parent_config_id` (infra).

### Terminate security (CI.md)

`server_halt()` preserves disk contents. **`snapshot/create` on a live session would seal secrets into a recoverable image.** `terminate_and_seal()` instead:

1. Optional `wipe_hook(subid)` — revoke Bitwarden, stop Docker, delete logs (while VM runs)
2. `server/halt` → `server/restore_snapshot` to the **baseline** SNAPSHOTID from boot
3. Record the baseline ID — never a new snapshot of dirty runtime state

## What we do NOT do (manual + soul.md)

- No arbitrary shell on Vultr API — templates/startup scripts only
- No API key in repo — `VULTR_API_KEY` + Bitwarden for agent secrets
- No v2 API in this module — **v1 per your manual** (v2 can be added later as separate client)

## Quick test (live account)

```bash
export VULTR_API_KEY=your_key
PYTHONPATH=. python3 -c "
from infra.vultr import VultrClient
c = VultrClient()
print(c.auth_info())
print('snapshots', len(c.snapshot_list()))
"
```
