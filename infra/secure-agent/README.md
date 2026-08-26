# Secure Agent Sandbox

Ephemeral agent runs with **Bitwarden-injected secrets**, **network allowlisting**,
**log redaction + encryption**, and optional **Firecracker microVM isolation** (Ignite).

Operates under [soul.md](../../soul.md) + [CI.md](../../CI.md): secrets never touch disk,
no custom shell from agent input, fail-closed on missing `BW_SESSION`.

## Isolation layers

```
┌─────────────────────────────────────────────────────────────┐
│  HOST (your machine / Kamatra VPS)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  LAYER 3 — Firecracker microVM (Ignite)  [optional]     │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  LAYER 2 — Docker internal network (secure_net) │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │  LAYER 1 — Ephemeral agent container      │  │  │  │
│  │  │  │  iptables OUTPUT allowlist only           │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│  Bitwarden CLI → secrets in memory only on host/VM          │
│  Logs → redact → Fernet encrypt → .enc (plaintext deleted)  │
└─────────────────────────────────────────────────────────────┘
```

| Runner | Isolation | When to use |
|--------|-----------|-------------|
| `agent_runner.sh` | Docker only | Dev / trusted host |
| `microvm_runner.sh` | Firecracker VM + Docker | Production / multi-tenant |

## Prerequisites

```bash
# Bitwarden CLI
npm install -g @bitwarden/cli
bw login your-email@example.com
export BW_SESSION=$(bw unlock --raw)

# Docker
docker info

# Optional — Ignite (Firecracker microVMs, Linux + KVM)
# https://github.com/weaveworks/ignite
curl -sfLo /usr/local/bin/ignite \
  https://github.com/weaveworks/ignite/releases/download/v0.10.0/ignite-amd64
chmod +x /usr/local/bin/ignite
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

chmod +x agent_runner.sh microvm_runner.sh cleanup_logs.sh

# Docker-only (Layer 1–2)
./agent_runner.sh

# Firecracker microVM (Layer 3) — recommended for production
./microvm_runner.sh
```

## What was wrong in the pasted scripts (fixed here)

| Issue | Fix |
|-------|-----|
| `$ (bw unlock` broken spacing | `$(bw unlock --raw)` |
| `$BN_SE` typo | `$BW_SESSION` |
| `1ogs` / `encrypt_1ogs.py` typos | `logs` / `encrypt_logs.py` |
| Plaintext log left on disk | Removed after encrypt |
| Secrets in env after run | `unset` + `trap cleanup` |
| No VM boundary | `microvm_runner.sh` via Ignite |

## AWS / Nitro Firecracker

On AWS bare metal (Nitro), Firecracker runs without Ignite:

1. Build the same OCI rootfs / kernel bundle as your Ignite image.
2. Use [firecracker-go-sdk](https://github.com/firecracker-microvm/firecracker-go-sdk) or
   your Infrastructure Hub Deployment Orchestrator to spawn microVMs via API.
3. Pass `BW_SESSION` only into the microVM bootstrap — revoke on terminate (CI.md lifecycle).

Kamatra VPS nodes can run `microvm_runner.sh` if `/dev/kvm` is available.

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
    "runner": "microvm_runner.sh",
    "vm_name": vm_name,
    "isolation": "firecracker+ docker",
}, actor="system")
```

## Security notes

- **Never** commit `allowed_hosts.txt` with production IPs if the repo is public.
- **Never** write `BW_SESSION` or secrets to disk or logs.
- `iptables` rules require `--privileged` on the container — acceptable inside a microVM;
  avoid privileged containers directly on the host when Ignite is available.
- Agent logic must not execute user-supplied shell — use templates only (soul.md Section II).
