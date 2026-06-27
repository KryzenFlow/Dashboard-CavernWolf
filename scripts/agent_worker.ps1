# Poll backend for research/blog jobs — run on your agent PC (STUDIO_MODE=internal).

param(
    [string]$ApiBase = $env:OPS_API_BASE,
    [int]$IntervalSeconds = 30,
    [switch]$Once
)

if (-not $ApiBase) { $ApiBase = "http://localhost:8000" }

function Invoke-OpsPost($Path) {
    $uri = "$ApiBase$Path"
    return Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json" -Body "{}"
}

Write-Host "Agent worker -> $ApiBase (Ctrl+C to stop)"

do {
    try {
        $result = Invoke-OpsPost "/ops/jobs/claim-and-run"
        if ($result.job) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Job #$($result.job.id) $($result.job.job_type) -> $($result.outcome.status)"
        } else {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] No pending jobs"
        }
    } catch {
        Write-Warning $_.Exception.Message
    }
    if ($Once) { break }
    Start-Sleep -Seconds $IntervalSeconds
} while ($true)
