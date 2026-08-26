#!/bin/bash
# One-time bootstrap for a fresh Vultr VPS (Ubuntu). No secrets on disk.
# Run as root on a new instance: curl ... | bash   OR   ./vultr_bootstrap.sh
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  ca-certificates curl git python3 python3-pip python3-venv \
  iptables

# Docker (official)
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

# Node.js 20 LTS (Bitwarden CLI)
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

if ! command -v bw >/dev/null 2>&1; then
  npm install -g @bitwarden/cli
fi

# App checkout path (adjust repo URL for your fork)
APP_DIR="${APP_DIR:-/opt/cavernwolf}"
if [[ ! -d "$APP_DIR/.git" ]]; then
  mkdir -p "$APP_DIR"
  echo "[INFO] Clone your repo into ${APP_DIR} manually or set APP_DIR."
fi

if [[ -f "${APP_DIR}/infra/secure-agent/requirements.txt" ]]; then
  pip3 install --break-system-packages -r "${APP_DIR}/infra/secure-agent/requirements.txt"
fi

echo "[OK] Vultr bootstrap complete."
echo "Next steps:"
echo "  1. Vultr firewall: allow SSH (22) from your IP only — block public agent ports"
echo "  2. ssh into VPS, clone repo to ${APP_DIR}"
echo "  3. bw login && export BW_SESSION=\$(bw unlock --raw)"
echo "  4. cd ${APP_DIR}/infra/secure-agent && ./agent_runner.sh"
