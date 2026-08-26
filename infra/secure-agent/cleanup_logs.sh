#!/bin/bash
# Remove encrypted logs older than retention window.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
DAYS_TO_KEEP="${DAYS_TO_KEEP:-7}"

find "$LOG_DIR" -type f -name "*.enc" -mtime "+${DAYS_TO_KEEP}" -exec rm -f {} \;
echo "[OK] Cleaned encrypted logs older than ${DAYS_TO_KEEP} days in ${LOG_DIR}"
