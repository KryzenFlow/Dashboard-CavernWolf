# Secure Agent Sandbox

Ephemeral agent runs with **Bitwarden-injected secrets**, **Docker isolation**,
**network allowlisting**, and **log redaction + encryption**.

Operates under [soul.md](../../soul.md) + [CI.md](../../CI.md): secrets never touch disk,
no custom shell from agent input, fail-closed on missing `BW_SESSION`.

## How it works (Docker)

```
┌─────────────────────────────────────────────────────────┐
│  HOST (Vultr VPS or local dev machine)                  │
│  ┌───────────────────────────────────────────────────┐│
│  │  Docker internal network (secure_net)             ││
│  │  ┌─────────────────────────────────────────────┐  ││
│  │  │  Ephemeral agent container                  │  ││
│  │  │  iptables OUTPUT allowlist only             │  ││
│  │  └─────────────────────────────────────────────┘  ││
│  └───────────────────────────────────────────────────┘│
│  Bitwarden CLI → secrets in memory only               │
│  Logs → redact → Fernet encrypt → .enc (plain deleted)│
└─────────────────────────────────────────────────────────┘
```

**Runner:** `./agent_runner.sh` — Docker on the host. Production target is a **Vultr VPS**.

## Vultr VPS deployment

Recommended instance: **Ubuntu 24.04 LTS**, 2 vCPU / 4 GB RAM (adjust for agent load).

### 1. Create the server

- Vultr control panel → Deploy → Cloud Compute → Ubuntu 24.04
- Enable **Vultr Firewall**: allow **SSH (22)** from your IP only
- Do **not** expose agent or Docker ports publicly — agents use outbound allowlist only

### 2. Bootstrap (once)

```bash
ssh root@YOUR_VULTR_IP
git clone https://github.com/KryzenFlow/Dashboard-CavernWolf.git /opt/cavernwolf
chmod +x /opt/cavernwolf/infra/secure-agent/vultr_bootstrap.sh
APP_DIR=/opt/cavernwolf /opt/cavernwolf/infra/secure-agent/vultr_bootstrap.sh
```

### 3. Run agents (each session)

```bash
ssh root@YOUR_VULTR_IP
export BW_SESSION=$(bw unlock --raw)
cd /opt/cavernwolf/infra/secure-agent
cp allowed_hosts.txt.example allowed_hosts.txt   # first time only
./agent_runner.sh
```

Bitwarden unlock happens on the Vultr box per session — secrets stay in memory, never in the image.

### Vultr notes

| Topic | Guidance |
|-------|----------|
| **API** | [Vultr API v1](../vultr/MANUAL_ALIGNMENT.md) — aligned with `source/vultr-api-reference-v1.pdf` |
| **Provider** | Vultr Cloud Compute (Docker-only) |
| **Firewall** | `FIREWALLGROUPID` on server create (manual) + container iptables allowlist |
| **Snapshots** | `snapshot/create` + `restore_snapshot` = CI.md `[IMAGE STORED]` + rollback |
| **Secrets** | `VULTR_API_KEY` for API; Bitwarden `BW_SESSION` for agent secrets |

Set `VULTR_API_KEY` from https://my.vultr.com/settings/#settingsapi (manual: API-Key header).

## Prerequisites (local or Vultr)

```bash
# Bitwarden CLI
npm install -g @bitwarden/cli
bw login your-email@example.com
export BW_SESSION=$(bw unlock --raw)

# Docker
docker info
```

## Bitwarden vault items

Create these items (password fields):

| Item name | Used for |
|-----------|----------|
| `sandbox-encryption-key` | Fernet key for log encryption |
| `project-db-password` | Agent DB credential |
| `project-api-key` | Agent API credential |

## Quick start

```bash
cd infra/secure-agent
pip install -r requirements.txt
cp allowed_hosts.txt.example allowed_hosts.txt
# edit allowed_hosts.txt — one host/IP per line

chmod +x agent_runner.sh cleanup_logs.sh
./agent_runner.sh
```

## What was fixed from the original scripts

| Issue | Fix |
|-------|-----|
| `$ (bw unlock` broken spacing | `$(bw unlock --raw)` |
| `$BN_SE` typo | `$BW_SESSION` |
| `1ogs` / `encrypt_1ogs.py` typos | `logs` / `encrypt_logs.py` |
| Plaintext log left on disk | Removed after encrypt |
| Secrets in env after run | `unset` + `trap cleanup` |

## Log retention

```bash
./cleanup_logs.sh   # default: delete *.enc older than 7 days
DAYS_TO_KEEP=14 ./cleanup_logs.sh
```

## Audit integration

Record runs in the Merkle audit ledger:

```python
from app.security.merkle import AuditLedger

ledger.record("AGENT_SANDBOX_RUN", {
    "runner": "agent_runner.sh",
    "isolation": "docker",
}, actor="system")
```

## Security notes

- **Never** commit `allowed_hosts.txt` with production IPs if the repo is public.
- **Never** write `BW_SESSION` or secrets to disk or logs.
- `iptables` rules require `--privileged` on the container.
- Agent logic must not execute user-supplied shell — use templates only (soul.md Section II).

## Future: microVM layer (not required)

`microvm_runner.sh` is kept for later if you want Firecracker/Ignite VM-level isolation
on top of Docker. **You do not need it now** — Docker-only is the supported path.
