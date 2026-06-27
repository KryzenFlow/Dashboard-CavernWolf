# Put Hermes data/ on OneDrive so memory.db, research.db, content.db sync/backup via M365.

param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$OneDriveRoot = $env:OneDrive
)

if (-not $OneDriveRoot) {
    Write-Error "OneDrive path not found. Set OneDrive env or pass -OneDriveRoot."
    exit 1
}

$HermesData = Join-Path $OneDriveRoot "HermesData"
$LocalData = Join-Path $RepoRoot "data"

New-Item -ItemType Directory -Force -Path $HermesData | Out-Null

# Move existing DB files if present and data is not already a junction
if ((Test-Path $LocalData) -and -not (Get-Item $LocalData).LinkType) {
    Get-ChildItem $LocalData -File | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $HermesData $_.Name) -Force
    }
    Remove-Item $LocalData -Recurse -Force
}

if (-not (Test-Path $LocalData)) {
    cmd /c mklink /J "$LocalData" "$HermesData" | Out-Null
    Write-Host "Linked: $LocalData -> $HermesData"
} else {
    Write-Host "data/ already exists at $LocalData"
}

Write-Host @"

OneDrive sync enabled for:
  - memory.db (agent memory)
  - research.db (job queue)
  - content.db (blog drafts)

On your OTHER PC:
  1. Clone the same repo
  2. Run this script (OneDrive will sync HermesData folder)
  3. Set STUDIO_MODE=internal in .env
  4. docker compose up --build
  5. .\scripts\agent_worker.ps1

Do NOT run docker on two PCs against the same DB files at the same time.
Stop stack on one PC before starting on the other, or use separate HermesData folders per machine.

"@