# V1.0 smoke test against running ai-copilot-serve
param(
    [string]$BaseUrl = "http://127.0.0.1:8765"
)

$ErrorActionPreference = "Stop"

Write-Host "health..."
Invoke-RestMethod -Uri "$BaseUrl/api/v1/health" | ConvertTo-Json

Write-Host "create profile..."
$profile = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/profiles" -ContentType "application/json" -Body '{"name":"default","type":"default"}'
$profile | ConvertTo-Json
$id = $profile.id

Write-Host "list profiles..."
Invoke-RestMethod -Uri "$BaseUrl/api/v1/profiles" | ConvertTo-Json -Depth 5

Write-Host "start profile (requires Hermes or mock gateway configured)..."
try {
    Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/profiles/$id/start" | ConvertTo-Json
} catch {
    Write-Warning "start failed (expected if Hermes CLI not installed): $_"
}

Write-Host "smoke done."
