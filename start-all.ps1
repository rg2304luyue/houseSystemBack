<#
.SYNOPSIS
    Start the house rental system's backend and frontend.

.EXAMPLE
    .\start-all.ps1
    Opens separate local development terminals for FastAPI and Vite.

.EXAMPLE
    .\start-all.ps1 -Mode Dev
    Opens separate local development terminals for FastAPI and Vite.
#>
[CmdletBinding()]
param(
    [ValidateSet('Dev')]
    [string]$Mode = 'Dev'
)

$ErrorActionPreference = 'Stop'
$backendRoot = $PSScriptRoot
$frontendRoot = Join-Path (Split-Path $backendRoot -Parent) 'houseSystemFront-Ylfmoonn'

if (-not (Test-Path (Join-Path $frontendRoot 'package.json'))) {
    throw "Frontend project was not found: $frontendRoot"
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Required command 'npm' was not found."
}

$pythonExecutable = Join-Path $backendRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExecutable)) {
    throw "Backend virtual environment was not found: $pythonExecutable"
}

Write-Host 'Applying database migrations...' -ForegroundColor Cyan
Push-Location $backendRoot
try {
    & $pythonExecutable -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Database migration failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

$backendCommand = "Set-Location -LiteralPath '$backendRoot'; & '$pythonExecutable' -m uvicorn app.main:app --reload --port 8000"
$frontendCommand = "Set-Location -LiteralPath '$frontendRoot'; npm run dev"

Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $backendCommand | Out-Null
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $frontendCommand | Out-Null

Write-Host ''
Write-Host 'Development servers are starting in two new terminals.' -ForegroundColor Green
Write-Host 'Frontend is normally available at http://localhost:4399'
Write-Host 'Backend is normally available at http://localhost:8000'
