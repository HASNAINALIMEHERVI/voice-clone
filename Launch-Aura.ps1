$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Start-Process powershell -WorkingDirectory (Join-Path $root "backend") -ArgumentList "-NoExit", "-Command", "python main.py"
Start-Process powershell -WorkingDirectory (Join-Path $root "frontend") -ArgumentList "-NoExit", "-Command", "npm run dev"
Write-Host "Open http://localhost:5173 after both servers start." -ForegroundColor Green
