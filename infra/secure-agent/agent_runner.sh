#!/bin/bash
# Run secure agent inside an ephemeral Docker container with Bitwarden-injected secrets.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALLOWED_HOSTS_FILE="${ALLOWED_HOSTS_FILE:-${SCRIPT_DIR}/allowed_hosts.txt}"
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
CONTAINER_NAME="secure_agent_$(date +%s)"
NETWORK_NAME="secure_net_${CONTAINER_NAME}"

if [[ -z "${BW_SESSION:-}" ]]; then
  echo "[ERROR] BW_SESSION is required. Run: export BW_SESSION=\$(bw unlock --raw)" >&2
  exit 1
fi

mkdir -p "$LOG_DIR"

# Secrets: memory only — pulled from Bitwarden, never written to disk
ENCRYPTION_KEY="$(bw get password "sandbox-encryption-key" --session "$BW_SESSION")"
DB_PASSWORD="$(bw get password "project-db-password" --session "$BW_SESSION")"
API_KEY="$(bw get password "project-api-key" --session "$BW_SESSION")"

LOG_FILE="${LOG_DIR}/${CONTAINER_NAME}.log"

cleanup() {
  docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
  docker network rm "$NETWORK_NAME" 2>/dev/null || true
  unset ENCRYPTION_KEY DB_PASSWORD API_KEY
}
trap cleanup EXIT

docker build -t secure-agent "${SCRIPT_DIR}"

docker network create --internal "$NETWORK_NAME" 2>/dev/null || true

docker run --rm \
  --name "$CONTAINER_NAME" \
  --network "$NETWORK_NAME" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e API_KEY="$API_KEY" \
  -v "${LOG_DIR}:/logs" \
  secure-agent > "$LOG_FILE" 2>&1 &
RUN_PID=$!

CONTAINER_ID=""
for _ in $(seq 1 30); do
  CONTAINER_ID="$(docker ps -qf "name=^${CONTAINER_NAME}$" || true)"
  [[ -n "$CONTAINER_ID" ]] && break
  sleep 0.5
done

if [[ -z "$CONTAINER_ID" ]]; then
  echo "[ERROR] Container failed to start. See ${LOG_FILE}" >&2
  wait "$RUN_PID" || true
  exit 1
fi

# Outbound allowlist — no internet except whitelisted hosts
if [[ -f "$ALLOWED_HOSTS_FILE" ]]; then
  while IFS= read -r host || [[ -n "$host" ]]; do
    host="${host%%#*}"
    host="$(echo "$host" | xargs)"
    [[ -z "$host" ]] && continue
    docker exec --privileged "$CONTAINER_ID" sh -c \
      "iptables -A OUTPUT -d ${host} -j ACCEPT" || true
  done < "$ALLOWED_HOSTS_FILE"
fi
docker exec --privileged "$CONTAINER_ID" sh -c "iptables -A OUTPUT -j DROP" || true

docker wait "$CONTAINER_ID" || true
wait "$RUN_PID" 2>/dev/null || true

python3 "${SCRIPT_DIR}/redact_logs.py" "$LOG_FILE"
python3 "${SCRIPT_DIR}/encrypt_logs.py" "$LOG_FILE" "$ENCRYPTION_KEY"

# Remove any plaintext remnant
rm -f "$LOG_FILE"

echo "[OK] Encrypted log: ${LOG_FILE}.enc"
