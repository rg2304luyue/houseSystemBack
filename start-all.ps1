<#
.SYNOPSIS
    Start the house rental system's backend and frontend.

.EXAMPLE
    .\start-all.ps1
    Starts the complete Docker environment in the background.

.EXAMPLE
    .\start-all.ps1 -Mode Dev
    Opens separate local development terminals for Flask and Vite.
#>
[CmdletBinding()]
param(
    [ValidateSet('Docker', 'Dev')]
    [string]$Mode = 'Docker'
)

$ErrorActionPreference = 'Stop'
$backendRoot = $PSScriptRoot
$frontendRoot = Join-Path (Split-Path $backendRoot -Parent) 'houseSystemFront-Ylfmoonn'

if (-not (Test-Path (Join-Path $frontendRoot 'package.json'))) {
    throw "Frontend project was not found: $frontendRoot"
}

if ($Mode -eq 'Docker') {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker was not found. Install and start Docker Desktop, or run .\start-all.ps1 -Mode Dev.'
    }

    Push-Location $backendRoot
    try {
        docker compose up -d --build
    }
    finally {
        Pop-Location
    }

    Write-Host ''
    Write-Host 'System started.' -ForegroundColor Green
    Write-Host 'Frontend: http://localhost'
    Write-Host 'Backend:  http://localhost:5000'
    Write-Host 'Stop it with: docker compose down (from the backend folder).'
    exit 0
}

foreach ($command in @('python', 'npm')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command '$command' was not found."
    }
}

$pythonExecutable = Join-Path $backendRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExecutable)) {
    $pythonExecutable = 'python'
}
$backendCommand = "Set-Location -LiteralPath '$backendRoot'; & '$pythonExecutable' app.py"
$frontendCommand = "Set-Location -LiteralPath '$frontendRoot'; npm run dev -- --host 0.0.0.0"

Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $backendCommand | Out-Null
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $frontendCommand | Out-Null

Write-Host ''
Write-Host 'Development servers are starting in two new terminals.' -ForegroundColor Green
Write-Host 'Frontend is normally available at http://localhost:5173'
Write-Host 'Backend is normally available at http://localhost:5000'
