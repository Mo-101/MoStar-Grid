# MoStar-Grid Master Startup Script

$ErrorActionPreference = "Continue"
$ScriptPath = $PSScriptRoot

Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "   MoStar-Grid: System Initialization     " -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta

# --- Configuration ---
$Neo4jStart = Join-Path $ScriptPath "backend\neo4j-mostar-industries\start-neo4j.ps1"
$VenvPath = Join-Path $ScriptPath ".venv\Scripts\Activate.ps1"
$PythonExe = Join-Path $ScriptPath ".venv\Scripts\python.exe"

# --- 1. Start Neo4j ---
Write-Host "`n[1/4] Starting Neo4j Database..." -ForegroundColor Cyan
if (Test-Path $Neo4jStart) {
    $ArgsList = "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $Neo4jStart
    Start-Process powershell -ArgumentList $ArgsList -WorkingDirectory (Join-Path $ScriptPath "backend\\neo4j-mostar-industries")
    Write-Host "   >> Neo4j window launched." -ForegroundColor Gray
}
else {
    Write-Warning "   !! Neo4j start script not found at $Neo4jStart"
}

Start-Sleep -Seconds 2

# --- 2. Start Memory Layer API (Port 8000) ---
Write-Host "`n[2/4] Starting Memory Layer API (Port 8000)..." -ForegroundColor Cyan
if (Test-Path $PythonExe) {
    $Cmd = '$env:PYTHONPATH="{0}"; Write-Host "Starting Memory API..."; & "{1}" -m uvicorn backend.memory_layer.api.main:app --reload --port 8000' -f $ScriptPath, $PythonExe
    $ArgsList = "-NoExit", "-Command", $Cmd
    Start-Process powershell -ArgumentList $ArgsList -WorkingDirectory $ScriptPath
    Write-Host "   >> Memory API window launched." -ForegroundColor Gray
}
else {
    Write-Warning "   !! Python executable not found at $PythonExe"
}

Start-Sleep -Seconds 2

# --- 3. Start Core Engine API (Port 8001) ---
Write-Host "`n[3/4] Starting Core Engine API (Port 8001)..." -ForegroundColor Cyan
if (Test-Path $PythonExe) {
    $Cmd = '$env:PYTHONPATH="{0}"; Write-Host "Starting Core Engine..."; & "{1}" -m uvicorn core_engine.api_gateway:app --reload --port 8001' -f $ScriptPath, $PythonExe
    $ArgsList = "-NoExit", "-Command", $Cmd
    Start-Process powershell -ArgumentList $ArgsList -WorkingDirectory $ScriptPath
    Write-Host "   >> Core Engine window launched." -ForegroundColor Gray
}
else {
    Write-Warning "   !! Python executable not found at $PythonExe"
}

Start-Sleep -Seconds 2

# --- 4. Start Frontend (Port 3000) ---
Write-Host "`n[4/4] Starting Frontend..." -ForegroundColor Cyan
$FrontendPath = Join-Path $ScriptPath "frontend"
if (Test-Path $FrontendPath) {
    $Cmd = 'Set-Location "{0}"; Write-Host "Starting Next.js Frontend..."; npm run dev' -f $FrontendPath
    $ArgsList = "-NoExit", "-Command", $Cmd
    Start-Process powershell -ArgumentList $ArgsList -WorkingDirectory $FrontendPath
    Write-Host "   >> Frontend window launched." -ForegroundColor Gray
}
else {
    Write-Warning "   !! Frontend directory not found at $FrontendPath"
}

Write-Host "`nSystem Startup Sequence Initiated." -ForegroundColor Green
