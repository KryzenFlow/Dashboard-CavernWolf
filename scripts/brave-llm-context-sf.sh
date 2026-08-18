#!/usr/bin/env bash
# Brave LLM Context — San Francisco local recall (37.7749, -122.4194)
#
# Default: gateway-compatible path on localhost (q is optional; gateway uses "near me").
# Direct Brave: BRAVE_HOST=https://api.search.brave.com ./scripts/brave-llm-context-sf.sh
set -euo pipefail

HOST="${BRAVE_HOST:-http://localhost:8000}"

header_args=()
if [[ -n "${BRAVE_SEARCH_API_KEY:-}" ]]; then
  header_args+=(-H "X-Subscription-Token: ${BRAVE_SEARCH_API_KEY}")
elif [[ "${HOST}" == *search.brave.com* ]]; then
  echo "Set BRAVE_SEARCH_API_KEY to call Brave directly." >&2
  exit 1
fi

curl -X GET "${HOST}/res/v1/llm/context" \
  "${header_args[@]}" \
  -H "X-Loc-Lat: 37.7749" \
  -H "X-Loc-Long: -122.4194"
