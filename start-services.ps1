# ==============================================================================
# MOSTAR GRID - UNIFIED SERVICE LAUNCHER
# Starts ALL services: Neo4j, Memory Layer, Core Engine, Mo Executor, Frontend
# ==============================================================================

$ErrorActionPreference = "Continue"
$ScriptPath = $PSScriptRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "   MoStar-Grid: Full System Boot          " -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta

# --- Configuration ---
$Neo4jStart   = Join-Path $ScriptPath "backend\neo4j-mostar-industries\start-neo4j.ps1"
$PythonExe    = Join-Path $ScriptPath ".venv\Scripts\python.exe"
$FrontendPath = Join-Path $ScriptPath "frontend"
$LogsDir      = Join-Path $ScriptPath "logs"
$ExecutorScript = Join-Path $ScriptPath "backend\mo_executor.py"

if (-not (Test-Path $LogsDir)) { New-Item -ItemType Directory -Path $LogsDir | Out-Null }

# --- Helper: Kill process on port ---
function Stop-PortProcess {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Where-Object { $_.State -eq "Listen" }
    if ($conn) {
        $procIds = $conn.OwningProcess | Sort-Object -Unique
        foreach ($p in $procIds) {
            $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "   >> Killing $($proc.ProcessName) (PID $p) on port $Port" -ForegroundColor Yellow
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Milliseconds 500
    }
}

# --- Helper: Launch a python uvicorn service in a new window ---
function Start-PythonService {
    param([string]$Title, [string]$Module, [string]$Port, [string]$LogFile)
    $encodedCmd = [Convert]::ToBase64String(
        [System.Text.Encoding]::Unicode.GetBytes(
            "`$env:PYTHONPATH = '$ScriptPath'; " +
            "`$env:PYTHONUTF8 = '1'; " +
            "Write-Host '=== $Title (port $Port) ==='; " +
            "& '$PythonExe' -m uvicorn $Module --host 0.0.0.0 --port $Port --reload " +
            "2>&1 | Tee-Object -FilePath '$LogFile'"
        )
    )
    Start-Process powershell -ArgumentList "-NoExit", "-EncodedCommand", $encodedCmd -WorkingDirectory $ScriptPath
}

# --- 0. Clear stale processes on all ports ---
Write-Host "`n[0/5] Clearing stale processes on ports 3000, 8000, 8001..." -ForegroundColor DarkYellow
Stop-PortProcess -Port 8000
Stop-PortProcess -Port 8001
Stop-PortProcess -Port 3000
Write-Host "   >> Ports cleared." -ForegroundColor Gray

# --- 1. Start Neo4j (Sovereign Soul) ---
Write-Host "`n[1/5] Starting Neo4j Database (ports 7474/7687)..." -ForegroundColor Cyan
$Neo4jAlive = $false
try {
    $Neo4jAlive = Test-NetConnection -ComputerName localhost -Port 7687 -WarningAction SilentlyContinue -InformationLevel Quiet
} catch {}

if ($Neo4jAlive) {
    Write-Host "   >> Neo4j already running on port 7687. Skipping." -ForegroundColor Green
} elseif (Test-Path $Neo4jStart) {
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $Neo4jStart `
        -WorkingDirectory (Join-Path $ScriptPath "backend\neo4j-mostar-industries")
    Write-Host "   >> Neo4j console window launched. Waiting for ready..." -ForegroundColor Gray
    $waited = 0
    while ($waited -lt 30) {
        Start-Sleep -Seconds 2
        $waited += 2
        try {
            if (Test-NetConnection -ComputerName localhost -Port 7687 -WarningAction SilentlyContinue -InformationLevel Quiet) {
                Write-Host "   >> Neo4j ready after ~${waited}s." -ForegroundColor Green
                break
            }
        } catch {}
    }
    if ($waited -ge 30) { Write-Warning "   !! Neo4j may not be ready yet. Continuing anyway." }
} else {
    Write-Warning "   !! Neo4j start script not found at $Neo4jStart"
}

# --- 2. Start Memory Layer API (Port 8000) ---
Write-Host "`n[2/5] Starting Memory Layer API (port 8000)..." -ForegroundColor Cyan
if (Test-Path $PythonExe) {
    $logFile = Join-Path $LogsDir "memory_layer.log"
    Start-PythonService -Title "Memory Layer API" -Module "backend.memory_layer.api.main:app" -Port "8000" -LogFile $logFile
    Write-Host "   >> Memory Layer window launched. Log: logs\memory_layer.log" -ForegroundColor Gray
} else {
    Write-Warning "   !! Python executable not found at $PythonExe"
}

Start-Sleep -Seconds 2

# --- 3. Start Core Engine API (Port 8001) ---
Write-Host "`n[3/5] Starting Core Engine API (port 8001)..." -ForegroundColor Cyan
if (Test-Path $PythonExe) {
    $logFile = Join-Path $LogsDir "core_engine.log"
    Start-PythonService -Title "Core Engine API" -Module "core_engine.api_gateway:app" -Port "8001" -LogFile $logFile
    Write-Host "   >> Core Engine window launched. Log: logs\core_engine.log" -ForegroundColor Gray
} else {
    Write-Warning "   !! Python executable not found at $PythonExe"
}

Start-Sleep -Seconds 2

# --- 4. Start Mo Executor (background daemon) ---
Write-Host "`n[4/5] Starting Mo Executor (graph mutation daemon)..." -ForegroundColor Cyan
if ((Test-Path $PythonExe) -and (Test-Path $ExecutorScript)) {
    $logFile = Join-Path $LogsDir "mo_executor.log"
    $encodedCmd = [Convert]::ToBase64String(
        [System.Text.Encoding]::Unicode.GetBytes(
            "`$env:PYTHONPATH = '$ScriptPath'; " +
            "`$env:PYTHONUTF8 = '1'; " +
            "`$env:NEO4J_URI = 'bolt://localhost:7687'; " +
            "`$env:NEO4J_USER = 'neo4j'; " +
            "`$env:NEO4J_PASSWORD = 'mostar123'; " +
            "Write-Host '=== Mo Executor (daemon) ==='; " +
            "& '$PythonExe' '$ExecutorScript' " +
            "2>&1 | Tee-Object -FilePath '$logFile'"
        )
    )
    Start-Process powershell -ArgumentList "-NoExit", "-EncodedCommand", $encodedCmd -WorkingDirectory $ScriptPath
    Write-Host "   >> Mo Executor window launched. Log: logs\mo_executor.log" -ForegroundColor Gray
} else {
    Write-Warning "   !! Mo Executor not found. Checked: $ExecutorScript"
}

Start-Sleep -Seconds 2

# --- 5. Start Next.js Frontend (Port 3000) ---
Write-Host "`n[5/5] Starting Next.js Frontend (port 3000)..." -ForegroundColor Cyan
if (Test-Path $FrontendPath) {
    $logFile = Join-Path $LogsDir "frontend.log"
    $encodedCmd = [Convert]::ToBase64String(
        [System.Text.Encoding]::Unicode.GetBytes(
            "Set-Location '$FrontendPath'; " +
            "Write-Host '=== Next.js Frontend (port 3000) ==='; " +
            "npm run dev 2>&1 | Tee-Object -FilePath '$logFile'"
        )
    )
    Start-Process powershell -ArgumentList "-NoExit", "-EncodedCommand", $encodedCmd -WorkingDirectory $FrontendPath
    Write-Host "   >> Frontend window launched. Log: logs\frontend.log" -ForegroundColor Gray
} else {
    Write-Warning "   !! Frontend directory not found at $FrontendPath"
}

# --- Summary ---
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  MoStar Grid - All Services Launched     " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Neo4j Browser   : http://localhost:7474  (neo4j / mostar123)" -ForegroundColor Cyan
Write-Host "  Memory Layer API: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Core Engine API : http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "  Mo Executor     : background daemon (logs\mo_executor.log)" -ForegroundColor Cyan
Write-Host "  Frontend UI     : http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Logs directory  : $LogsDir" -ForegroundColor DarkGray
Write-Host "==========================================" -ForegroundColor Green
