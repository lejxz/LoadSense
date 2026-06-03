$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

$env:PYTHONPATH = $Root

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Root'; `$env:PYTHONPATH='.'; & '$Python' -m uvicorn backend.app.main:app --reload"
)

Start-Sleep -Seconds 3

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Root'; & '$Python' edge\mock_telemetry.py --mode http --url http://127.0.0.1:8000/api/telemetry --interval 1"
)

Write-Host "LoadSense demo starting:"
Write-Host "  Launcher: http://127.0.0.1:8000/"
Write-Host "  Mobile:   http://127.0.0.1:8000/mobile.html"
Write-Host "  Operator: http://127.0.0.1:8000/operator.html"
