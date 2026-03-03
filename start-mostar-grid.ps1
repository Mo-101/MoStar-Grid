# ==============================================================================
# MOSTAR GRID — MASTER STARTUP SCRIPT
# The Flame Architect — MSTR-⚡
# Automatically launches the SOVEREIGN SOUL (Neo4j), API (FastAPI), and UI (Next.js)
# ==============================================================================

$ErrorActionPreference = "Continue"
$ScriptPath = $PSScriptRoot

Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "   MoStar-Grid: Unified System Boot       " -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta

# --- 1. Start Neo4j (Sovereign Soul) ---
Write-Host "`n[1/3] Initiating Sovereign Soul (Neo4j)..." -ForegroundColor Cyan
$Neo4jStart = Join-Path $ScriptPath "backend\neo4j-mostar-industries\start-neo4j.ps1"

if (Test-Path $Neo4jStart) {
    # Start Neo4j in a new window
    $ArgsList = "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $Neo4jStart
    Start-Process powershell -ArgumentList $ArgsList -WorkingDirectory (Join-Path $ScriptPath "backend\neo4j-mostar-industries")
    Write-Host "   >> Neo4j Graph Database window launched." -ForegroundColor Gray
}
else {
    Write-Warning "   !! Neo4j start script not found at $Neo4jStart"
}

Start-Sleep -Seconds 4

# --- 2. Start Unified Backend API (Port 7001) ---
Write-Host "`n[2/3] Initiating MoStar API Gateway (Port 7001)..." -ForegroundColor Cyan
$BackendDir = Join-Path $ScriptPath "backend"
$PythonExe = Join-Path $ScriptPath ".venv\Scripts\python.exe"

if (Test-Path $PythonExe) {
    # Launch main.py
    $Cmd = '$env:PYTHONPATH="{0}"; Write-Host "Starting MoStar API on Port 7001..."; & "{1}" main.py' -f $BackendDir, $PythonExe
    $ArgsList = "-NoExit", "-Command", $Cmd
    Start-Process powershell -ArgumentList $ArgsList -WorkingDirectory $BackendDir
    Write-Host "   >> API Gateway window launched." -ForegroundColor Gray
}
else {
    Write-Warning "   !! Python executable not found at $PythonExe"
}

Start-Sleep -Seconds 3

# --- 3. Start Next.js Frontend (Port 3000) ---
Write-Host "`n[3/3] Initiating MoStar User Interface (Port 3000)..." -ForegroundColor Cyan
$FrontendDir = Join-Path $ScriptPath "frontend"

if (Test-Path $FrontendDir) {
    $Cmd = 'Write-Host "Starting Next.js Frontend on Port 3000..."; npm run dev'
    $ArgsList = "-NoExit", "-Command", $Cmd
    Start-Process powershell -ArgumentList $ArgsList -WorkingDirectory $FrontendDir
    Write-Host "   >> Grid Frontend window launched." -ForegroundColor Gray
}
else {
    Write-Warning "   !! Frontend directory not found at $FrontendDir"
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "✅ MoStar Grid is Online." -ForegroundColor Green
Write-Host "🌐 Access UI at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Green
