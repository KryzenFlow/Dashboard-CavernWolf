# Start 2-container stack (structure + claw only, no token burn)
Set-Location (Split-Path -Parent $PSScriptRoot)
Write-Host "Minimal stack: backend + agent-claw (mock LLM, no agent pool)" -ForegroundColor Cyan
docker compose -f docker-compose.minimal.yml up --build
