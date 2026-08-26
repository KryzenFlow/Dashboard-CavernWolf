#!/bin/bash
# Ephemeral agent entrypoint — runs inside Docker container.
set -euo pipefail

echo "[agent] starting secure sandbox"
echo "[agent] DB configured: ${DB_PASSWORD:+yes}"
echo "[agent] API configured: ${API_KEY:+yes}"

# Replace with your agent logic — no shell injection from user input
python3 - <<'PY'
import os
import time

print("[agent] heartbeat")
time.sleep(2)
print("[agent] complete")
PY

echo "[agent] done" >> "/logs/agent-run.log" 2>&1 || true
