#!/usr/bin/env bash
# Dashboard-CavernWolf — one-shot Hermes Stack bootstrap (Linux / macOS / Git Bash)
# Run from repo root:  bash scripts/setup_stack.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Hermes Stack bootstrap ==="
echo "Repo root: $ROOT"

# --- 1. Folder structure (safe — does not overwrite code) ---
DIRS=(
  backend backend/agents/reasoning backend/agents/memory backend/agents/orchestration
  backend/web_gateway backend/routes backend/tests
  agent_claw frontend llama_stub
  templates/static-site templates/react-app templates/landing-page
  models shared/workflows data scripts .github/workflows
)
for d in "${DIRS[@]}"; do
  mkdir -p "$d"
done
touch models/.gitkeep data/.gitkeep shared/workflows/.gitkeep 2>/dev/null || true

# --- 2. Environment file ---
if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "  copied .env.example -> .env"
  else
    echo "  warning: .env.example missing"
  fi
else
  echo "  .env already exists (skipped)"
fi

# --- 3. Docker check ---
if ! command -v docker &>/dev/null; then
  echo "Docker not found. Install Docker, then: docker compose up --build"
  exit 1
fi
if ! docker info &>/dev/null; then
  echo "Docker daemon not running. Start Docker, then: docker compose up --build"
  exit 1
fi

# --- 4. Validate compose ---
echo "  validating docker-compose.yml ..."
docker compose config >/dev/null

# --- 5. Start stack ---
echo ""
echo "Starting full stack..."
echo "  Studio:  http://localhost:3000"
echo "  Backend: http://localhost:8000/health"
echo "  Claw:    http://localhost:9000/health"
echo ""
docker compose up --build
