# Verify Hermes stack after docker compose up
# Usage: .\scripts\verify_stack.ps1

$ErrorActionPreference = "Continue"
$ok = 0
$fail = 0

function Test-Endpoint($Name, $Url) {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) {
            Write-Host "[OK] $Name - $Url" -ForegroundColor Green
            $script:ok++
        } else {
            Write-Host "[FAIL] $Name - HTTP $($r.StatusCode)" -ForegroundColor Red
            $script:fail++
        }
    } catch {
        Write-Host "[FAIL] $Name - $($_.Exception.Message)" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "=== Hermes Stack health check ===" -ForegroundColor Cyan
Write-Host ""

Test-Endpoint "Hermes Studio" "http://localhost:3000"
Test-Endpoint "Backend root" "http://localhost:8000/"
Test-Endpoint "Backend health" "http://localhost:8000/health"
Test-Endpoint "Agent Claw" "http://localhost:9000/health"
Test-Endpoint "LLaMA stub" "http://localhost:8080/health"

Write-Host ""
try {
    $body = '{"query":"hello stack"}'
    $reason = Invoke-RestMethod -Uri "http://localhost:8000/reason" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 90
    if ($reason.answer) {
        Write-Host "[OK] POST /reason - got answer" -ForegroundColor Green
        $ok++
    } else {
        Write-Host "[FAIL] POST /reason - no answer field" -ForegroundColor Red
        $fail++
    }
} catch {
    Write-Host "[FAIL] POST /reason - $($_.Exception.Message)" -ForegroundColor Red
    $fail++
}

Write-Host ""
Write-Host "Results: $ok passed, $fail failed"
if ($fail -gt 0) { exit 1 }
