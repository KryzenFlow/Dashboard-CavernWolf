# Copy notes from USB (Good2Go) into repo inbox for Cursor to review.
# Usage: .\scripts\ingest_usb_notes.ps1
#        .\scripts\ingest_usb_notes.ps1 -UsbRoot "G:\"

param(
    [string]$UsbRoot = "G:\",
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent)
)

$inbox = Join-Path $RepoRoot "docs\inbox\usb-good2go"
New-Item -ItemType Directory -Force -Path $inbox | Out-Null

if (-not (Test-Path $UsbRoot)) {
    Write-Error "USB not found at $UsbRoot. Plug in Good2Go USB and retry."
    exit 1
}

$extensions = @("*.txt", "*.md", "*.pdf")
$copied = 0
foreach ($ext in $extensions) {
    Get-ChildItem -Path $UsbRoot -Filter $ext -File -ErrorAction SilentlyContinue | ForEach-Object {
        $dest = Join-Path $inbox $_.Name
        Copy-Item $_.FullName $dest -Force
        $copied++
    }
}

Write-Host "Copied $copied files to $inbox"
Write-Host "Tell Cursor: 'Review docs/inbox/usb-good2go and merge best ideas into the repo.'"
