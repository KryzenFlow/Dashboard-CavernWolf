<#
.SYNOPSIS
  Doberman.ps1 — local Ollama guard wrapper with redacted telemetry.

.DESCRIPTION
  Intercepts a local reasoning request, validates the payload, applies a
  simple rate limit, calls Ollama, and writes telemetry JSON (no secrets)
  for a Studio status bar. This does NOT replace Claw Opus. Claw uses
  OPENCLAW_GATEWAY_URL only.

.NOTES
  DeepSeek Architect rule: never emit tokens, BW_SESSION, HMAC keys, or
  Authorization headers into telemetry or logs.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Prompt,

    [string]$OllamaUrl = $(if ($env:OLLAMA_URL) { $env:OLLAMA_URL } else { "http://127.0.0.1:11434" }),

    [string]$Model = $(if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "llama3.2" }),

    [int]$MaxPromptChars = 32000,

    [int]$MinIntervalMs = 500,

    [string]$TelemetryPath = $(if ($env:DOBERMAN_TELEMETRY_PATH) { $env:DOBERMAN_TELEMETRY_PATH } else { Join-Path $env:TEMP "doberman-telemetry.json" })
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-DobermanTelemetry {
    param(
        [hashtable]$Data
    )
    # Strip any accidental secret-looking fields
    foreach ($key in @("token", "password", "authorization", "api_key", "BW_SESSION", "HMAC")) {
        if ($Data.ContainsKey($key)) {
            $Data.Remove($key)
        }
    }
    $Data["ts"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $Data["guard"] = "Doberman.ps1"
    $json = $Data | ConvertTo-Json -Depth 6 -Compress
    $dir = Split-Path -Parent $TelemetryPath
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    Set-Content -Path $TelemetryPath -Value $json -Encoding utf8
    # Also emit one line for status-bar readers (stdout)
    Write-Output $json
}

function Test-DobermanPayload {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) {
        throw "Doberman: empty prompt"
    }
    if ($Text.Length -gt $MaxPromptChars) {
        throw "Doberman: prompt exceeds MaxPromptChars ($MaxPromptChars)"
    }
    if ($Text -match "-----BEGIN (?:RSA |EC |OPENSSH |PRIVATE )?KEY-----") {
        throw "Doberman: private key material blocked"
    }
    if ($Text -match "(?i)\b(bw_session|api[_-]?key|authorization:\s*bearer)\b") {
        throw "Doberman: secret-like content blocked from local model prompt"
    }
}

# Rate limit (process-local via timestamp file)
$rateFile = Join-Path $env:TEMP "doberman-last-call.tick"
$now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
if (Test-Path $rateFile) {
    $last = [int64](Get-Content $rateFile -Raw)
    $delta = $now - $last
    if ($delta -lt $MinIntervalMs) {
        Write-DobermanTelemetry @{
            status   = "rate_limited"
            model    = $Model
            wait_ms  = ($MinIntervalMs - $delta)
            prompt_n = $Prompt.Length
        }
        exit 3
    }
}
Set-Content -Path $rateFile -Value "$now" -Encoding ascii

try {
    Test-DobermanPayload -Text $Prompt
}
catch {
    Write-DobermanTelemetry @{
        status   = "blocked"
        reason   = $_.Exception.Message
        model    = $Model
        prompt_n = $Prompt.Length
    }
    throw
}

$body = @{
    model  = $Model
    prompt = $Prompt
    stream = $false
} | ConvertTo-Json -Compress

$uri = ($OllamaUrl.TrimEnd("/") + "/api/generate")
$sw = [System.Diagnostics.Stopwatch]::StartNew()

try {
    $response = Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body -TimeoutSec 120
    $sw.Stop()
    $text = [string]$response.response
    Write-DobermanTelemetry @{
        status      = "ok"
        model       = $Model
        latency_ms  = $sw.ElapsedMilliseconds
        prompt_n    = $Prompt.Length
        response_n  = $text.Length
        # Never include prompt/response bodies in telemetry (leak surface)
    }
    # Model text on stderr so stdout stays telemetry-only for status bar
    [Console]::Error.WriteLine($text)
    exit 0
}
catch {
    $sw.Stop()
    Write-DobermanTelemetry @{
        status     = "error"
        model      = $Model
        latency_ms = $sw.ElapsedMilliseconds
        prompt_n   = $Prompt.Length
        reason     = "ollama_unreachable_or_failed"
        # Do not echo exception messages that might include URLs with tokens
    }
    exit 2
}
