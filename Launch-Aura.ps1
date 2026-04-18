# Aura AI One-Click Launcher
# This script starts the backend and frontend simultaneously.

Write-Host "🚀 Manifesting Aura AI..." -ForegroundColor Cyan

# 1. Start Backend in a new window
Write-Host "📡 Starting Neural Engine (Backend)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py" -WindowStyle Normal

# 2. Start Frontend in a new window
Write-Host "🎨 Starting Sonic Ether (Frontend)..." -ForegroundColor Purple
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -WindowStyle Normal

Write-Host "✅ Aura AI is materializing!" -ForegroundColor Green
Write-Host "🔗 Open your browser at http://localhost:5173" -ForegroundColor Yellow

# Wait a few seconds then open browser
Start-Sleep -Seconds 5
Start-Process "http://localhost:5173"
