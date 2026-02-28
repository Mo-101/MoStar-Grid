[CmdletBinding()]
param(
    [switch]$StopDocker,
    [switch]$IgnoreDocker,
    [switch]$AllowPortConflict,
    [switch]$Preflight,
    [string]$JdkHome,
    [string]$SetInitialPassword
)

$ErrorActionPreference = "Continue"

function Get-JavaMajorFromText {
    param([string]$JavaVersionText)

    if ($JavaVersionText -match '"(?<major>\d+)(?:\.\d+)*"') {
        return [int]$Matches.major
    }

    if ($JavaVersionText -match '\b(?<major>\d+)\.\d+(?:\.\d+)?\b') {
        return [int]$Matches.major
    }

    return $null
}

function Get-JavaVersionText {
    param([string]$JavaExe)

    try {
        return (& $JavaExe --version 2>&1 | Out-String).Trim()
    }
    catch {
        return $null
    }
}

function Resolve-BundledJdk21 {
    param([string]$RepoRoot)

    $toolsDir = Join-Path $RepoRoot ".tools"
    $jdkDir = Join-Path $toolsDir "jdk-21.0.5+11"
    $javaExe = Join-Path $jdkDir "bin\\java.exe"
    $zipPath = Join-Path $RepoRoot "jdk21.zip"

    if (Test-Path $javaExe) {
        return $jdkDir
    }

    if (-not (Test-Path $zipPath)) {
        return $null
    }

    if (-not (Test-Path $toolsDir)) {
        New-Item -ItemType Directory -Path $toolsDir -ErrorAction Stop | Out-Null
    }

    Write-Host "Extracting bundled JDK 21 from `"$zipPath`" -> `"$toolsDir`" ..." -ForegroundColor Cyan
    Expand-Archive -LiteralPath $zipPath -DestinationPath $toolsDir -Force -ErrorAction Stop

    if (Test-Path $javaExe) {
        return $jdkDir
    }

    return $null
}

function Stop-MostarDockerNeo4jIfRunning {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return
    }

    $containerId = (docker ps -q --filter "name=mostar-neo4j") 2>$null
    if (-not $containerId) {
        return
    }

    Write-Host "Stopping Docker container `mostar-neo4j` (ports 7474/7687)..." -ForegroundColor Yellow
    docker stop mostar-neo4j | Out-Null
}

function Assert-Neo4jPortsFree {
    if ($AllowPortConflict) {
        return
    }

    $listeners = Get-NetTCPConnection -State Listen -LocalPort 7474, 7687 -ErrorAction SilentlyContinue
    if (-not $listeners) {
        return
    }

    $rows = $listeners |
        Select-Object LocalAddress, LocalPort, OwningProcess -Unique |
        ForEach-Object {
            $pid = $_.OwningProcess
            $procName = "?"
            $procPath = "?"
            try {
                $p = Get-Process -Id $pid -ErrorAction Stop
                $procName = $p.ProcessName
                $procPath = $p.Path
            }
            catch { }

            [pscustomobject]@{
                LocalPort = $_.LocalPort
                LocalAddress = $_.LocalAddress
                PID = $pid
                Process = $procName
                Path = $procPath
            }
        }

    Write-Host "Neo4j can't start because these ports are already in use:" -ForegroundColor Red
    $rows | Format-Table -AutoSize | Out-String | Write-Host
    Write-Host "Fix: stop whatever is using 7474/7687 (often Docker `mostar-neo4j`) and retry." -ForegroundColor Yellow
    exit 3
}

$neo4jHome = (Resolve-Path $PSScriptRoot).Path
$repoRoot = (Resolve-Path (Join-Path $neo4jHome "..\\..")).Path

if (-not $Preflight) {
    if (-not $IgnoreDocker -and $StopDocker) {
        Stop-MostarDockerNeo4jIfRunning
    }

    if (-not $IgnoreDocker -and -not $StopDocker -and (Get-Command docker -ErrorAction SilentlyContinue)) {
        $containerId = (docker ps -q --filter "name=mostar-neo4j") 2>$null
        if ($containerId) {
            Write-Host "Docker container `mostar-neo4j` is running and will block local Neo4j (7474/7687)." -ForegroundColor Yellow
            Write-Host "Stop it with: `docker stop mostar-neo4j`  (or run this script with `-StopDocker`)" -ForegroundColor Yellow
            exit 2
        }
    }

    Assert-Neo4jPortsFree
}

$selectedJavaHome = $null

if ($JdkHome) {
    $candidate = (Resolve-Path $JdkHome -ErrorAction Stop).Path
    $javaExe = Join-Path $candidate "bin\\java.exe"
    if (-not (Test-Path $javaExe)) {
        throw "Provided -JdkHome does not contain bin\\java.exe: $candidate"
    }
    $selectedJavaHome = $candidate
}
else {
    $bundled = Resolve-BundledJdk21 -RepoRoot $repoRoot
    if ($bundled) {
        $selectedJavaHome = $bundled
    }
}

if (-not $selectedJavaHome) {
    Write-Host "No Java 21 found." -ForegroundColor Red
    Write-Host "Fix options:" -ForegroundColor Yellow
    Write-Host "  1) Install a system JDK 21 and ensure `java -version` is 21.x" -ForegroundColor Yellow
    Write-Host "  2) Keep `jdk21.zip` at repo root (already present) and rerun this script" -ForegroundColor Yellow
    Write-Host "  3) Run with -JdkHome <path-to-jdk-21>" -ForegroundColor Yellow
    exit 1
}

$javaExe = Join-Path $selectedJavaHome "bin\\java.exe"
$javaText = Get-JavaVersionText -JavaExe $javaExe
if (-not $javaText) {
    throw "Failed to execute Java at $javaExe"
}

$javaMajor = Get-JavaMajorFromText -JavaVersionText $javaText
if (-not $javaMajor -or $javaMajor -lt 21) {
    Write-Host "Selected Java is not 21+: $javaText" -ForegroundColor Red
    Write-Host "Fix: point -JdkHome at JDK 21 (or let the bundled JDK extract)." -ForegroundColor Yellow
    exit 1
}

$env:JAVA_HOME = $selectedJavaHome
$env:Path = (Join-Path $selectedJavaHome "bin") + ";" + $env:Path

Write-Host "JAVA_HOME = $env:JAVA_HOME" -ForegroundColor Green
Write-Host $javaText -ForegroundColor DarkGray

$neo4jAdminBat = Join-Path $neo4jHome "bin\\neo4j-admin.bat"
if (-not (Test-Path $neo4jAdminBat)) {
    throw "Neo4j admin script not found: $neo4jAdminBat"
}

if ($Preflight) {
    Write-Host "Preflight OK: Java 21+ selected; invoking Neo4j admin version..." -ForegroundColor Cyan
    & $neo4jAdminBat --version
    exit $LASTEXITCODE
}

if ($SetInitialPassword) {
    Write-Host "Setting initial Neo4j password..." -ForegroundColor Cyan
    & $neo4jAdminBat dbms set-initial-password $SetInitialPassword
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to set initial password (exit $LASTEXITCODE)."
    }
}

Write-Host "Starting local Neo4j (community) from $neo4jHome" -ForegroundColor Cyan
Write-Host "HTTP: http://localhost:7474  |  Bolt: bolt://localhost:7687" -ForegroundColor Cyan
& $neo4jAdminBat server console
