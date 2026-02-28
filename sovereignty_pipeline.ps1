<#
.SYNOPSIS
  MoStar Grid Sovereignty Pipeline: Scan + Report + (Optional) Clean + (Optional) Hash Lock + (Optional) CI Hook + (Optional) Lockdown

.DESCRIPTION
  - Scans for "contamination" indicators (SDKs, URLs, requirements, package.json, env files, orchestrator/router markers)
  - Generates dependency graphs (pipdeptree, npm ls) when available
  - Runs static analysis (bandit, eslint) when available
  - Optional: removes contaminated dependencies (pip/npm)
  - Optional: generates and verifies SHA256 manifest (GRID_HASHES.sha256)
  - Optional: installs git pre-commit hook to block commits if audit fails
  - Optional: applies outbound firewall lockdown rules (Windows only, requires admin)

.DEFAULTS
  Safe by default: no cleaning, no firewall changes, no hash locking unless explicitly enabled.

.NOTES
  Run from repository root.
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = ".",
  [switch]$Clean,
  [switch]$HashLock,
  [switch]$VerifyHashes,
  [switch]$InstallPreCommitHook,
  [switch]$Lockdown,            # Windows firewall outbound lockdown (admin required)
  [switch]$FailOnFindings,       # If set, any finding causes non-zero exit
  [string]$HashManifest = "GRID_HASHES.sha256",
  [string]$ReportDir = "sovereignty_reports",
  [string[]]$AllowDomains = @("localhost", "127.0.0.1", "mostar", "remostar"),
  [string[]]$ContaminatedTerms = @(
    # SDK/package names
    "openai","anthropic","langchain","cohere","mistral","groq","huggingface",
    # common endpoints / patterns
    "api.openai.com","anthropic.com","cohere.ai","huggingface.co","groq.com","mistral.ai",
    # runtime hints
    "OPENAI_API_KEY","ANTHROPIC_API_KEY","COHERE_API_KEY","HUGGINGFACEHUB_API_TOKEN",
    # suspicious patterns
    "eval(","Invoke-WebRequest","curl ","wget ","requests.get","http://","https://"
  ),
  [string[]]$KeyFilesToLock = @(
    "backend/core_engine/orchestrator.py",
    "backend/core_engine/remostar_smart_router.py",
    "backend/services/truth_engine_service.py"
  )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Helpers ---
function Write-Section($title) {
  Write-Host ""
  Write-Host ("=" * 90) -ForegroundColor DarkGray
  Write-Host ("  " + $title) -ForegroundColor Cyan
  Write-Host ("=" * 90) -ForegroundColor DarkGray
}

function Test-Command($name) {
  return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Ensure-Dir($path) {
  if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

function Add-Finding {
  param([string]$Category, [string]$Message, [string]$File = "", [int]$Line = 0)
  $global:Findings += [pscustomobject]@{
    time     = (Get-Date).ToString("s")
    category = $Category
    message  = $Message
    file     = $File
    line     = $Line
  }
}

function Save-Json($obj, $path) {
  $obj | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 $path
}

function Is-Admin {
  try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { return $false }
}

# --- Setup ---
$RepoRoot = (Resolve-Path $RepoRoot).Path
Push-Location $RepoRoot

Ensure-Dir $ReportDir
$global:Findings = @()
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$reportBase = Join-Path $ReportDir "sovereignty_$timestamp"

Write-Section "MoStar Grid Sovereignty Pipeline"
Write-Host "RepoRoot: $RepoRoot"
Write-Host "Report:   $reportBase"
$modeParts = @()
if($Clean) { $modeParts += "CLEAN" } else { $modeParts += "dry" }
if($HashLock) { $modeParts += "HASHLOCK" }
if($VerifyHashes) { $modeParts += "VERIFYHASH" }
if($InstallPreCommitHook) { $modeParts += "PRECOMMIT" }
if($Lockdown) { $modeParts += "LOCKDOWN" }
Write-Host "Mode:     $($modeParts -join ' ')" -ForegroundColor Yellow

# --- 1) Deep Scan: file content + key indicators ---
Write-Section "1) Deep Scan (content + indicators)"

# Files to scan (expand as needed)
$ScanGlobs = @(
  "*.ps1","*.py","*.ts","*.tsx","*.js","*.json","*.yaml","*.yml","*.toml","*.ini","*.env","Dockerfile","docker-compose*.yml","requirements*.txt","package*.json","pnpm-lock.yaml","yarn.lock","poetry.lock"
)

# Gather candidate files
$files = Get-ChildItem -Path $RepoRoot -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object {
    $n = $_.Name
    foreach($g in $ScanGlobs) {
      if ($n -like $g) { return $true }
    }
    return $false
  }

Write-Host "Scanning $($files.Count) files for contamination terms..."

foreach ($f in $files) {
  try {
    # skip huge binaries just in case (sane limit)
    if ($f.Length -gt 20MB) { continue }
    $content = Get-Content $f.FullName -ErrorAction SilentlyContinue
    if (-not $content) { continue }

    for ($i=0; $i -lt $content.Count; $i++) {
      $line = $content[$i]
      foreach ($term in $ContaminatedTerms) {
        if ($line -match [regex]::Escape($term)) {
          Add-Finding -Category "ContentMatch" -Message "Matched term: '$term'" -File $f.FullName -Line ($i+1)
        }
      }
    }
  } catch {
    Add-Finding -Category "ReadError" -Message $_.Exception.Message -File $f.FullName -Line 0
  }
}

# Explicit scans for common dependency manifests
$reqFiles = Get-ChildItem -Path $RepoRoot -Recurse -File -Include "requirements*.txt" -ErrorAction SilentlyContinue
foreach ($rf in $reqFiles) {
  $txt = Get-Content $rf.FullName -ErrorAction SilentlyContinue
  if ($txt) {
    foreach($term in @("openai","anthropic","langchain","cohere","mistral","groq","huggingface")) {
      if ($txt -match "(?im)^\s*$term(\b|==|>=|<=|~=)") {
        Add-Finding -Category "Requirements" -Message "Dependency present: $term" -File $rf.FullName -Line 0
      }
    }
  }
}

$pkgFiles = Get-ChildItem -Path $RepoRoot -Recurse -File -Include "package.json" -ErrorAction SilentlyContinue
foreach ($pf in $pkgFiles) {
  try {
    $json = Get-Content $pf.FullName -Raw | ConvertFrom-Json
    $deps = @()
    if ($json.dependencies) { $deps += $json.dependencies.PSObject.Properties.Name }
    if ($json.devDependencies) { $deps += $json.devDependencies.PSObject.Properties.Name }
    foreach($term in @("openai","anthropic","langchain","cohere","mistral","groq","huggingface")) {
      if ($deps -contains $term) {
        Add-Finding -Category "PackageJson" -Message "Dependency present: $term" -File $pf.FullName -Line 0
      }
    }
  } catch {
    Add-Finding -Category "PackageJsonError" -Message $_.Exception.Message -File $pf.FullName -Line 0
  }
}

# --- 2) Static analysis (optional based on availability) ---
Write-Section "2) Static Analysis (best-effort)"

# bandit (Python)
if (Test-Command "bandit") {
  $banditOut = "$reportBase.bandit.txt"
  Write-Host "Running bandit..."
  & bandit -r $RepoRoot 2>&1 | Tee-Object -FilePath $banditOut | Out-Null
  Add-Finding -Category "StaticAnalysis" -Message "Bandit report saved: $banditOut"
} else {
  Add-Finding -Category "StaticAnalysis" -Message "bandit not found; skipping."
}

# eslint (Node)
# We try npx eslint if eslint isn't in PATH.
$eslintOut = "$reportBase.eslint.txt"
if (Test-Command "eslint") {
  Write-Host "Running eslint..."
  & eslint "." 2>&1 | Tee-Object -FilePath $eslintOut | Out-Null
  Add-Finding -Category "StaticAnalysis" -Message "ESLint report saved: $eslintOut"
} elseif (Test-Command "npx") {
  Write-Host "Running npx eslint (if configured)..."
  & npx eslint "." 2>&1 | Tee-Object -FilePath $eslintOut | Out-Null
  Add-Finding -Category "StaticAnalysis" -Message "npx ESLint report saved: $eslintOut"
} else {
  Add-Finding -Category "StaticAnalysis" -Message "eslint/npx not found; skipping."
}

# --- 3) Dependency graphs ---
Write-Section "3) Dependency Graphs (pipdeptree / npm ls)"

# pipdeptree
$pipDepsOut = "$reportBase.deps_python.txt"
if (Test-Command "pipdeptree") {
  Write-Host "Generating pipdeptree..."
  & pipdeptree 2>&1 | Out-File -Encoding UTF8 $pipDepsOut
  Add-Finding -Category "DependencyGraph" -Message "pipdeptree saved: $pipDepsOut"
} elseif (Test-Command "pip") {
  Add-Finding -Category "DependencyGraph" -Message "pipdeptree not found; install via: pip install pipdeptree"
} else {
  Add-Finding -Category "DependencyGraph" -Message "pip not found; skipping Python dep graph."
}

# npm ls
$npmDepsOut = "$reportBase.deps_node.txt"
if (Test-Command "npm") {
  Write-Host "Generating npm ls (may be noisy)..."
  & npm ls 2>&1 | Out-File -Encoding UTF8 $npmDepsOut
  Add-Finding -Category "DependencyGraph" -Message "npm ls saved: $npmDepsOut"
} else {
  Add-Finding -Category "DependencyGraph" -Message "npm not found; skipping Node dep graph."
}

# --- 4) Automated Clean (optional) ---
Write-Section "4) Automated Clean (optional)"
$pyBad = @("anthropic","openai","langchain","cohere","mistral","groq","huggingface")
$nodeBad = @("anthropic","openai","langchain","cohere","mistral","groq","huggingface")

if ($Clean) {
  Write-Host "CLEAN enabled: attempting uninstall of known contaminated packages..." -ForegroundColor Yellow

  if (Test-Command "pip") {
    foreach ($p in $pyBad) {
      try {
        Write-Host "pip uninstall -y $p"
        & pip uninstall -y $p 2>&1 | Out-Null
      } catch {
        Add-Finding -Category "CleanError" -Message "pip uninstall failed for $p : $($_.Exception.Message)"
      }
    }
  } else {
    Add-Finding -Category "CleanError" -Message "pip not found; cannot uninstall Python packages."
  }

  if (Test-Command "npm") {
    foreach ($n in $nodeBad) {
      try {
        Write-Host "npm uninstall $n"
        & npm uninstall $n 2>&1 | Out-Null
      } catch {
        Add-Finding -Category "CleanError" -Message "npm uninstall failed for $n : $($_.Exception.Message)"
      }
    }
  } else {
    Add-Finding -Category "CleanError" -Message "npm not found; cannot uninstall Node packages."
  }

  Add-Finding -Category "Clean" -Message "Clean phase executed."
} else {
  Write-Host "Clean disabled (dry). No packages removed." -ForegroundColor DarkGray
}

# --- 5) Codex Integrity: Hash Lock & Verify ---
Write-Section "5) Codex Integrity (Hash lock / verify)"

function Compute-Manifest {
  param([string[]]$paths, [string]$outFile)

  $rows = @()
  foreach ($rel in $paths) {
    $full = Join-Path $RepoRoot $rel
    if (-not (Test-Path $full)) {
      Add-Finding -Category "HashLock" -Message "Missing file to hash: $rel"
      continue
    }
    $h = (Get-FileHash -Algorithm SHA256 -Path $full).Hash.ToLower()
    $rows += "$h  $rel"
  }
  $rows | Out-File -Encoding ASCII $outFile
}

function Verify-Manifest {
  param([string]$manifestPath)

  if (-not (Test-Path $manifestPath)) {
    Add-Finding -Category "HashVerify" -Message "Manifest not found: $manifestPath"
    return $false
  }

  $ok = $true
  $lines = Get-Content $manifestPath -ErrorAction SilentlyContinue
  foreach ($line in $lines) {
    if ($line -match "^\s*([0-9a-fA-F]{64})\s{2}(.+)\s*$") {
      $expected = $Matches[1].ToLower()
      $rel = $Matches[2].Trim()
      $full = Join-Path $RepoRoot $rel
      if (-not (Test-Path $full)) {
        Add-Finding -Category "HashVerify" -Message "Missing hashed file: $rel"
        $ok = $false
        continue
      }
      $actual = (Get-FileHash -Algorithm SHA256 -Path $full).Hash.ToLower()
      if ($actual -ne $expected) {
        Add-Finding -Category "HashVerify" -Message "HASH MISMATCH: $rel" -File $full -Line 0
        $ok = $false
      }
    }
  }
  return $ok
}

$manifestFull = Join-Path $RepoRoot $HashManifest

if ($HashLock) {
  Write-Host "HASHLOCK enabled: generating $HashManifest from key files..." -ForegroundColor Yellow
  Compute-Manifest -paths $KeyFilesToLock -outFile $manifestFull
  Add-Finding -Category "HashLock" -Message "Manifest generated: $manifestFull"
}

if ($VerifyHashes) {
  Write-Host "VERIFYHASH enabled: verifying $HashManifest..." -ForegroundColor Yellow
  $verified = Verify-Manifest -manifestPath $manifestFull
  if ($verified) {
    Add-Finding -Category "HashVerify" -Message "Manifest verification PASSED."
  } else {
    Add-Finding -Category "HashVerify" -Message "Manifest verification FAILED."
  }
}

# --- 6) CI/CD enforcement: pre-commit hook ---
Write-Section "6) CI Hook (pre-commit) (optional)"

if ($InstallPreCommitHook) {
  $gitDir = Join-Path $RepoRoot ".git"
  if (-not (Test-Path $gitDir)) {
    Add-Finding -Category "PreCommit" -Message "Not a git repo (.git not found). Skipping hook install."
  } else {
    $hooksDir = Join-Path $gitDir "hooks"
    Ensure-Dir $hooksDir
    $hookPath = Join-Path $hooksDir "pre-commit"

    # Use pwsh if available; fallback to powershell
    $shell = if (Test-Command "pwsh") { "pwsh" } else { "powershell" }

    $hook = @"
#!/bin/sh
# MoStar Sovereignty Gate - block commits if audit fails
$shell -NoProfile -ExecutionPolicy Bypass -File ./sovereignty_pipeline.ps1 -FailOnFindings
if [ \$? -ne 0 ]; then
  echo "Sovereignty audit failed. Commit blocked."
  exit 1
fi
exit 0
"@

    $hook | Out-File -Encoding ASCII $hookPath
    try { & git update-index --chmod=+x $hookPath 2>$null | Out-Null } catch {}
    Add-Finding -Category "PreCommit" -Message "Installed pre-commit hook: $hookPath"
  }
} else {
  Write-Host "Pre-commit hook install disabled." -ForegroundColor DarkGray
}

# --- 7) Lockdown: Windows outbound firewall rules (optional) ---
Write-Section "7) Lockdown (Windows Firewall outbound) (optional)"

if ($Lockdown) {
  if ($IsWindows -and (Is-Admin)) {
    Write-Host "Applying outbound firewall lockdown rules (Windows, admin)..." -ForegroundColor Yellow

    # Strategy (simple, practical):
    # - Create a rule group "MoStarGrid-Sovereignty"
    # - Allow outbound to allowed domains/IPs (note: Windows firewall can't allow by hostname directly for all cases)
    # - Block outbound to public internet broadly for target processes isn't trivial without app-based rules.
    # So: we apply a conservative rule: block outbound for common dev runtimes unless local.
    # You should tailor to your exact binaries/services in production.

    $group = "MoStarGrid-Sovereignty"

    # Cleanup old rules in group
    Get-NetFirewallRule -Group $group -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue

    # Allow outbound to localhost
    New-NetFirewallRule -DisplayName "MoStar Allow Localhost Outbound" -Direction Outbound -Action Allow -Group $group `
      -RemoteAddress "127.0.0.1","::1" -Profile Any | Out-Null

    # Allow outbound to private networks (adjust if you want strict)
    New-NetFirewallRule -DisplayName "MoStar Allow Private RFC1918 Outbound" -Direction Outbound -Action Allow -Group $group `
      -RemoteAddress "10.0.0.0/8","172.16.0.0/12","192.168.0.0/16" -Profile Any | Out-Null

    # Block outbound to internet (broad) - this is heavy-handed and may break updates/package installs.
    # Consider scoping to specific program paths (python.exe/node.exe) or container networks.
    New-NetFirewallRule -DisplayName "MoStar Block Public Outbound" -Direction Outbound -Action Block -Group $group `
      -RemoteAddress "0.0.0.0/0" -Profile Any | Out-Null

    Add-Finding -Category "Lockdown" -Message "Windows firewall lockdown rules applied (group: $group)."
    Add-Finding -Category "Lockdown" -Message "NOTE: This is intentionally strict; tailor to your service binaries and network model."
  } else {
    Add-Finding -Category "Lockdown" -Message "Lockdown requested but not supported (need Windows + admin). Skipping."
  }
} else {
  Write-Host "Lockdown disabled." -ForegroundColor DarkGray
}

# --- Save reports ---
Write-Section "Reporting"
$findingsJson = "$reportBase.findings.json"
$findingsTxt  = "$reportBase.findings.txt"

Save-Json $global:Findings $findingsJson

$global:Findings |
  Sort-Object category, file, line |
  Format-Table -AutoSize |
  Out-String |
  Out-File -Encoding UTF8 $findingsTxt

Write-Host "Saved: $findingsJson"
Write-Host "Saved: $findingsTxt"

# Summary counts
$counts = $global:Findings | Group-Object category | Sort-Object Name | Select-Object Name, Count
$counts | Format-Table -AutoSize

# Decide exit code
$exitCode = 0

# Findings that should be treated as "real contamination" (tune this)
$badCats = @("Requirements","PackageJson","ContentMatch","HashVerify")
$hasBad = $global:Findings | Where-Object { $badCats -contains $_.category } | Measure-Object | Select-Object -ExpandProperty Count

if ($VerifyHashes) {
  $hashFail = $global:Findings | Where-Object { $_.category -eq "HashVerify" -and $_.message -match "FAILED|MISMATCH" } | Measure-Object | Select-Object -ExpandProperty Count
  if ($hashFail -gt 0) { $exitCode = 2 }
}

if ($FailOnFindings -and $hasBad -gt 0) { $exitCode = 1 }

Write-Host ""
Write-Host "ExitCode: $exitCode" -ForegroundColor Yellow

Pop-Location
exit $exitCode
