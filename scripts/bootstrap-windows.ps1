# Single-repo Windows bootstrap: venv, deps, .env, migrate
param(
    [string]$RepoRoot = $PSScriptRoot + "\..",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path $RepoRoot).Path
Set-Location $RepoRoot

function Test-Python312 {
    $candidates = @(
        @{ Cmd = "py"; Args = @("-3.12", "--version") },
        @{ Cmd = "python"; Args = @("--version") }
    )
    foreach ($c in $candidates) {
        try {
            $out = & $c.Cmd @($c.Args) 2>&1 | Out-String
            if ($out -match "3\.12") { return $c }
        } catch { }
    }
    throw "Python 3.12 not found. Install Python 3.12.x and ensure 'py -3.12' or 'python' works."
}

function Ensure-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { return }
    Write-Host "Installing uv..."
    & py -3.12 -m pip install uv
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv not found after install attempt"
    }
}

Write-Host "== bootstrap-windows =="
Write-Host "Repo: $RepoRoot"

$py = Test-Python312
Write-Host "Python OK: $($py.Cmd) $($py.Args -join ' ')"

Ensure-Uv

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if ($Force -and (Test-Path (Join-Path $RepoRoot ".venv"))) {
    Remove-Item -Recurse -Force (Join-Path $RepoRoot ".venv")
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating venv..."
    & uv venv --python 3.12
}

Write-Host "uv sync --extra service..."
& uv sync --extra service

$envFile = Join-Path $RepoRoot ".env"
if ($Force -or -not (Test-Path $envFile)) {
    Write-Host "Writing .env from .env.example..."
    Copy-Item (Join-Path $RepoRoot ".env.example") $envFile -Force
}

Write-Host "alembic upgrade head..."
& uv run alembic upgrade head

Write-Host "Bootstrap complete. Start with:"
Write-Host "  uv run uvicorn main:app --app-dir src --host 127.0.0.1 --port 8765"
