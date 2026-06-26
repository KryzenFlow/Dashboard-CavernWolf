# Dashboard-CavernWolf - one-shot Hermes Stack bootstrap (Windows)
# Run from repo root:  .\scripts\setup_stack.ps1
# Or:                 powershell -ExecutionPolicy Bypass -File .\scripts\setup_stack.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== Hermes Stack bootstrap ===" -ForegroundColor Cyan
Write-Host "Repo root: $Root"

# --- 1. Folder structure (safe - does not overwrite code) ---
$dirs = @(
    "backend", "backend/agents/reasoning", "backend/agents/memory",
    "backend/agents/orchestration", "backend/web_gateway", "backend/routes",
    "backend/tests", "agent_claw", "frontend", "llama_stub",
    "templates/static-site", "templates/react-app", "templates/landing-page",
    "models", "shared/workflows", "data", "scripts", ".github/workflows"
)
foreach ($d in $dirs) {
    $path = Join-Path $Root $d
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  created $d"
    }
}
@("models/.gitkeep", "data/.gitkeep", "shared/workflows/.gitkeep") | ForEach-Object {
    $p = Join-Path $Root $_
    if (-not (Test-Path $p)) { New-Item -ItemType File -Path $p -Force | Out-Null }
}

# --- 2. Environment file ---
$envExample = Join-Path $Root ".env.example"
$envFile = Join-Path $Root ".env"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "  copied .env.example to .env" -ForegroundColor Green
    } else {
        Write-Warning ".env.example missing - create .env manually"
    }
} else {
    Write-Host "  .env already exists (skipped)"
}

# --- 3. Docker check ---
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host ""
    Write-Host "Docker not found. Install Docker Desktop, start it, then run:" -ForegroundColor Yellow
    Write-Host "  docker compose up --build"
    exit 1
}
try {
    docker info 2>&1 | Out-Null
} catch {
    Write-Host ""
    Write-Host "Docker is installed but not running. Start Docker Desktop, then run:" -ForegroundColor Yellow
    Write-Host "  docker compose up --build"
    exit 1
}

# --- 4. Validate compose ---
Write-Host "  validating docker-compose.yml ..."
docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# --- 5. Optional: local Python tests ---
if (Get-Command python -ErrorAction SilentlyContinue) {
    $req = Join-Path $Root "backend\requirements.txt"
    if (Test-Path $req) {
        Write-Host "  tip: run backend tests with:" -ForegroundColor DarkGray
        Write-Host "    cd backend; pip install -r requirements.txt; pytest tests/ -q" -ForegroundColor DarkGray
    }
}

# --- 6. Start stack ---
Write-Host ""
Write-Host "Starting full stack (Hermes Studio + agents + claw + memory)..." -ForegroundColor Cyan
Write-Host '  Studio:  http://localhost:3000'
Write-Host '  Backend: http://localhost:8000/health'
Write-Host '  Claw:    http://localhost:9000/health'
Write-Host ""

docker compose up --build
