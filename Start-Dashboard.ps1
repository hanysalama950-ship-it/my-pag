param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$dashboardUrl = 'http://127.0.0.1:8765/'
$pythonExe = 'C:\Users\HQ_2026_QH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$dashboardHealthy = $false
try {
    $health = Invoke-RestMethod -Uri ($dashboardUrl + 'health') -TimeoutSec 2
    if ($health.app -ne 'ceo-followup-local') { throw 'Port 8765 is occupied by another app.' }
    $dashboardHealthy = $true
} catch { }
if (-not $dashboardHealthy) {
    if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Python runtime is missing. Ask Codex to repair the dashboard launcher.' }
    $serverPath = Join-Path $PSScriptRoot 'local\server.py'
    $localDir = Join-Path $PSScriptRoot 'local'
    Start-Process -FilePath $pythonExe -ArgumentList @('-X','utf8',('"'+$serverPath+'"')) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $localDir 'server.log') -RedirectStandardError (Join-Path $localDir 'server-error.log') | Out-Null
    for ($attempt=0; $attempt -lt 10; $attempt++) {
        Start-Sleep -Milliseconds 300
        try { $health = Invoke-RestMethod -Uri ($dashboardUrl+'health') -TimeoutSec 1; if ($health.app -eq 'ceo-followup-local') { $dashboardHealthy=$true; break } } catch { }
    }
    if (-not $dashboardHealthy) { throw 'Local dashboard did not start. Check local/server-error.log.' }
}
if (-not $NoBrowser) { Start-Process $dashboardUrl }
Write-Output $dashboardUrl
