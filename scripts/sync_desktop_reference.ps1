# Copy loose Desktop spec exports into docs/reference/desktop-export/
# Safe to re-run — overwrites files in that folder only.

$Source = "$env:USERPROFILE\OneDrive\Desktop\New Project Workspace\Data for Dashboard all loose files and some have Vellorae"
$Dest = Join-Path $PSScriptRoot "..\docs\reference\desktop-export" | Resolve-Path -ErrorAction SilentlyContinue
if (-not $Dest) {
    $Dest = Join-Path (Split-Path $PSScriptRoot -Parent) "docs\reference\desktop-export"
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
}

if (-not (Test-Path $Source)) {
    Write-Error "Source folder not found: $Source"
    exit 1
}

Copy-Item -Path "$Source\*" -Destination $Dest -Recurse -Force
Write-Host "Synced $(@(Get-ChildItem $Dest).Count) files to $Dest"
Write-Host "See docs/reference/README.md - do not paste .txt exports into backend code."
