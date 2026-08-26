#!/bin/bash
# OPTIONAL — future microVM layer (Ignite/Firecracker). Not required; use agent_runner.sh for Docker-only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_NAME="${VM_NAME:-secure_agent_vm_$(date +%s)}"
IGNITE_IMAGE="${IGNITE_IMAGE:-weaveworks/ignite-ubuntu}"
VM_CPUS="${VM_CPUS:-2}"
VM_MEMORY="${VM_MEMORY:-2GB}"
VM_DISK="${VM_DISK:-6GB}"

if ! command -v ignite >/dev/null 2>&1; then
  echo "[ERROR] ignite CLI not found. Install: https://github.com/weaveworks/ignite" >&2
  exit 1
fi

if [[ -z "${BW_SESSION:-}" ]]; then
  echo "[ERROR] BW_SESSION is required on the host before VM boot." >&2
  exit 1
fi

# Pack runner + scripts into VM — no secrets in the copy set
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"; ignite rm -f "$VM_NAME" 2>/dev/null || true' EXIT

cp -a "${SCRIPT_DIR}/agent_runner.sh" \
      "${SCRIPT_DIR}/redact_logs.py" \
      "${SCRIPT_DIR}/encrypt_logs.py" \
      "${SCRIPT_DIR}/Dockerfile" \
      "${SCRIPT_DIR}/run_agent.sh" \
      "$STAGING/"

if [[ -f "${SCRIPT_DIR}/allowed_hosts.txt" ]]; then
  cp "${SCRIPT_DIR}/allowed_hosts.txt" "$STAGING/"
else
  cp "${SCRIPT_DIR}/allowed_hosts.txt.example" "$STAGING/allowed_hosts.txt"
fi

echo "[BOOT] Starting Firecracker microVM via Ignite: ${VM_NAME}"

ignite run "$IGNITE_IMAGE" \
  --name "$VM_NAME" \
  --cpus "$VM_CPUS" \
  --memory "$VM_MEMORY" \
  --size "$VM_DISK" \
  --copy-files "${STAGING}/agent_runner.sh:/opt/secure-agent/agent_runner.sh" \
  --copy-files "${STAGING}/redact_logs.py:/opt/secure-agent/redact_logs.py" \
  --copy-files "${STAGING}/encrypt_logs.py:/opt/secure-agent/encrypt_logs.py" \
  --copy-files "${STAGING}/Dockerfile:/opt/secure-agent/Dockerfile" \
  --copy-files "${STAGING}/run_agent.sh:/opt/secure-agent/run_agent.sh" \
  --copy-files "${STAGING}/allowed_hosts.txt:/opt/secure-agent/allowed_hosts.txt"

# Inside VM: install docker + bw if missing, pass BW_SESSION for this run only
ignite exec "$VM_NAME" -- bash -lc "
  set -euo pipefail
  export BW_SESSION='${BW_SESSION}'
  export DEBIAN_FRONTEND=noninteractive
  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
  fi
  if ! command -v bw >/dev/null 2>&1; then
    npm install -g @bitwarden/cli
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    apt-get update && apt-get install -y python3 python3-pip
  fi
  pip3 install --quiet cryptography
  chmod +x /opt/secure-agent/*.sh
  cd /opt/secure-agent && ./agent_runner.sh
"

echo "[SEAL] MicroVM run complete. Tearing down ${VM_NAME}."
ignite rm -f "$VM_NAME"
