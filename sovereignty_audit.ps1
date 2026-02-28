param(
    [switch]$Clean,
    [switch]$DependencyGraph,
    [switch]$StaticAnalysis,
    [switch]$GenerateHashes,
    [switch]$VerifyHashes,
    [switch]$InstallHook,
    [switch]$Lockdown,
    [switch]$ApplyFirewall,
    [switch]$NoFailOnFindings
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$ReportsDir = Join-Path $RepoRoot "reports\sovereignty"
New-Item -Path $ReportsDir -ItemType Directory -Force | Out-Null

$Findings = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

$ForbiddenPythonPackages = @(
    "anthropic",
    "openai",
    "langchain",
    "cohere",
    "mistralai",
    "groq",
    "huggingface_hub",
    "transformers"
)

$ForbiddenNodePackages = @(
    "@anthropic-ai/sdk",
    "openai",
    "langchain",
    "cohere-ai",
    "@mistralai/mistralai",
    "groq-sdk",
    "@huggingface/inference"
)

$ForbiddenHosts = @(
    "api.openai.com",
    "api.anthropic.com",
    "api.cohere.ai",
    "api.mistral.ai",
    "api.groq.com",
    "huggingface.co"
)

$SovereignFiles = @(
    "backend/core_engine/orchestrator.py",
    "backend/core_engine/api_gateway.py",
    "backend/remostar_smart_router.py",
    "backend/sacred_handshake.py",
    "backend/truth_engine/truth_engine_service.py",
    "backend/start_grid.py"
)

$HashFile = Join-Path $RepoRoot "backend\sovereign_hashes.json"

function Write-Section {
    param([string]$Name)
    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
}

function Add-Finding {
    param([string]$Message)
    $Findings.Add($Message) | Out-Null
    Write-Host "[FINDING] $Message" -ForegroundColor Yellow
}

function Add-Warning {
    param([string]$Message)
    $Warnings.Add($Message) | Out-Null
    Write-Host "[WARN] $Message" -ForegroundColor DarkYellow
}

function Get-Rg {
    return Get-Command rg -ErrorAction SilentlyContinue
}

function Find-Pattern {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Pattern,
        [string[]]$Globs = @("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.mjs", "*.cjs", "*.json", "*.env", "*.toml", "*.yml", "*.yaml")
    )

    $results = @()
    $rg = Get-Rg
    if ($rg) {
        $args = @(
            "-n",
            "--hidden",
            "--glob", "!**/.git/**",
            "--glob", "!**/node_modules/**",
            "--glob", "!**/.venv/**",
            "--glob", "!**/__pycache__/**"
        )
        foreach ($g in $Globs) {
            $args += @("-g", $g)
        }
        $args += @("-e", $Pattern, ".")
        $results = & rg @args 2>$null
        $exitCode = $LASTEXITCODE
        if ($exitCode -gt 1) {
            Add-Warning "ripgrep failed for '$Label' (exit $exitCode)."
            return
        }
    }
    else {
        $targets = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch "\\\.git\\" -and
                $_.FullName -notmatch "\\node_modules\\" -and
                $_.FullName -notmatch "\\\.venv\\" -and
                $_.FullName -notmatch "\\__pycache__\\"
            } |
            Where-Object {
                $file = $_.Name
                foreach ($g in $Globs) {
                    if ($file -like $g) { return $true }
                }
                return $false
            }

        foreach ($file in $targets) {
            $matches = Select-String -Path $file.FullName -Pattern $Pattern -ErrorAction SilentlyContinue
            foreach ($m in $matches) {
                $results += "{0}:{1}:{2}" -f $m.Path, $m.LineNumber, $m.Line.Trim()
            }
        }
    }

    $resultLines = @($results)
    if ($resultLines.Count -gt 0) {
        $outFile = Join-Path $ReportsDir ("{0}.txt" -f ($Label -replace "[^a-zA-Z0-9_-]", "_"))
        $resultLines | Set-Content -Path $outFile
        Add-Finding "$Label -> $($resultLines.Count) matches. Report: $outFile"
    }
}

function Scan-Manifests {
    Write-Section "Manifest Scan"

    $reqFiles = Get-ChildItem -Recurse -File -Include "requirements*.txt", "pyproject.toml", "Pipfile", "Pipfile.lock" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "\\\.venv\\" -and $_.FullName -notmatch "\\node_modules\\" }

    foreach ($file in $reqFiles) {
        $lines = Get-Content $file.FullName -ErrorAction SilentlyContinue
        foreach ($pkg in $ForbiddenPythonPackages) {
            $hit = $lines | Select-String -Pattern ("(?i)\b{0}\b" -f [regex]::Escape($pkg))
            if ($hit) {
                Add-Finding "Python dependency '$pkg' appears in $($file.FullName)"
            }
        }
    }

    $pkgFiles = Get-ChildItem -Recurse -File -Filter "package.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "\\node_modules\\" }

    foreach ($file in $pkgFiles) {
        try {
            $json = Get-Content $file.FullName -Raw | ConvertFrom-Json
        }
        catch {
            Add-Warning "Could not parse $($file.FullName): $($_.Exception.Message)"
            continue
        }

        $depTables = @()
        foreach ($propName in @("dependencies", "devDependencies", "optionalDependencies")) {
            if ($json.PSObject.Properties.Name -contains $propName) {
                $depTables += ,$json.$propName
            }
        }
        foreach ($table in $depTables) {
            if (-not $table) { continue }
            foreach ($pkg in $ForbiddenNodePackages) {
                if ($table.PSObject.Properties.Name -contains $pkg) {
                    Add-Finding "Node dependency '$pkg' appears in $($file.FullName)"
                }
            }
        }
    }
}

function Run-DeepScan {
    Write-Section "Deep Scan"

    $pyImportPattern = "(?i)^\s*(from|import)\s+(anthropic|openai|langchain|cohere|mistralai|groq|huggingface_hub|transformers)\b"
    $jsImportPattern = "(?i)(from|require\()\s*['""](@anthropic-ai/sdk|openai|langchain|cohere-ai|@mistralai/mistralai|groq-sdk|@huggingface/inference)['""]"
    $urlPattern = "(?i)https?://(api\.openai\.com|api\.anthropic\.com|api\.cohere\.ai|api\.mistral\.ai|api\.groq\.com|huggingface\.co)"

    Find-Pattern -Label "python_forbidden_imports" -Pattern $pyImportPattern -Globs @("*.py")
    Find-Pattern -Label "node_forbidden_imports" -Pattern $jsImportPattern -Globs @("*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs", "*.cjs")
    Find-Pattern -Label "forbidden_hosts_in_code" -Pattern $urlPattern

    Scan-Manifests
}

function Run-DependencyGraph {
    Write-Section "Dependency Graph"

    if (Get-Command pipdeptree -ErrorAction SilentlyContinue) {
        pipdeptree | Set-Content (Join-Path $ReportsDir "deps_python.txt")
        Write-Host "Python dependency graph written to reports\sovereignty\deps_python.txt"
    }
    else {
        Add-Warning "pipdeptree not found. Install with: pip install pipdeptree"
    }

    if (Get-Command npm -ErrorAction SilentlyContinue) {
        if (Test-Path (Join-Path $RepoRoot "package.json")) {
            cmd /c "npm ls --all > `"$ReportsDir\deps_node_root.txt`" 2>&1"
        }
        if (Test-Path (Join-Path $RepoRoot "frontend\package.json")) {
            cmd /c "npm --prefix frontend ls --all > `"$ReportsDir\deps_node_frontend.txt`" 2>&1"
        }
        Write-Host "Node dependency graph reports written under reports\sovereignty\"
    }
    else {
        Add-Warning "npm not found. Skipping Node dependency graph."
    }
}

function Run-StaticAnalysis {
    Write-Section "Static Analysis"

    if (Get-Command bandit -ErrorAction SilentlyContinue) {
        $banditOut = Join-Path $ReportsDir "bandit_backend.txt"
        & bandit -r backend -f txt -o $banditOut
        $banditExit = $LASTEXITCODE
        if ($banditExit -ne 0) {
            Add-Finding "bandit reported issues (exit $banditExit). Report: $banditOut"
        }
        else {
            Write-Host "bandit passed. Report: $banditOut"
        }
    }
    else {
        Add-Warning "bandit not found. Install with: pip install bandit"
    }

    if (Get-Command npm -ErrorAction SilentlyContinue) {
        $frontendPkg = Join-Path $RepoRoot "frontend\package.json"
        if (Test-Path $frontendPkg) {
            $lintLog = Join-Path $ReportsDir "eslint_frontend.txt"
            cmd /c "npm --prefix frontend run -s lint > `"$lintLog`" 2>&1"
            if ($LASTEXITCODE -ne 0) {
                Add-Finding "eslint/frontend reported issues (exit $LASTEXITCODE). Report: $lintLog"
            }
            else {
                Write-Host "eslint/frontend passed. Report: $lintLog"
            }
        }
        else {
            Add-Warning "frontend/package.json not found. Skipping eslint."
        }
    }
    else {
        Add-Warning "npm not found. Skipping eslint."
    }
}

function Run-Clean {
    Write-Section "Automated Clean"

    if (Get-Command pip -ErrorAction SilentlyContinue) {
        try {
            & pip uninstall -y @($ForbiddenPythonPackages)
            Write-Host "Python cleanup command executed."
        }
        catch {
            Add-Warning "Python cleanup failed: $($_.Exception.Message)"
        }
    }
    else {
        Add-Warning "pip not found. Skipping Python cleanup."
    }

    if (Get-Command npm -ErrorAction SilentlyContinue) {
        if (Test-Path (Join-Path $RepoRoot "package.json")) {
            cmd /c "npm uninstall @anthropic-ai/sdk openai langchain cohere-ai @mistralai/mistralai groq-sdk @huggingface/inference" | Out-Null
        }
        if (Test-Path (Join-Path $RepoRoot "frontend\package.json")) {
            cmd /c "npm --prefix frontend uninstall @anthropic-ai/sdk openai langchain cohere-ai @mistralai/mistralai groq-sdk @huggingface/inference" | Out-Null
        }
        Write-Host "Node cleanup command executed."
    }
    else {
        Add-Warning "npm not found. Skipping Node cleanup."
    }
}

function Get-SovereignHashSet {
    $items = @()
    foreach ($rel in $SovereignFiles) {
        $full = Join-Path $RepoRoot $rel
        if (-not (Test-Path $full)) {
            Add-Warning "Sovereign hash target not found: $rel"
            continue
        }
        $h = Get-FileHash -Algorithm SHA256 -Path $full
        $items += [PSCustomObject]@{
            path = $rel
            sha256 = $h.Hash
        }
    }
    return $items
}

function Generate-HashLock {
    Write-Section "Hash Lock Generate"
    $payload = [PSCustomObject]@{
        generated_utc = (Get-Date).ToUniversalTime().ToString("o")
        files = Get-SovereignHashSet
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $HashFile
    Write-Host "Hash manifest written to $HashFile"
}

function Verify-HashLock {
    Write-Section "Hash Lock Verify"
    if (-not (Test-Path $HashFile)) {
        Add-Finding "Hash manifest missing: $HashFile"
        return
    }

    $expected = Get-Content $HashFile -Raw | ConvertFrom-Json
    $currentByPath = @{}
    foreach ($entry in (Get-SovereignHashSet)) {
        $currentByPath[$entry.path] = $entry.sha256
    }

    foreach ($entry in $expected.files) {
        if (-not $currentByPath.ContainsKey($entry.path)) {
            Add-Finding "Hash verify missing file: $($entry.path)"
            continue
        }
        if ($currentByPath[$entry.path] -ne $entry.sha256) {
            Add-Finding "Hash mismatch: $($entry.path)"
        }
    }
}

function Install-PreCommitHook {
    Write-Section "Git Hook Install"
    $hookDir = Join-Path $RepoRoot ".git\hooks"
    if (-not (Test-Path $hookDir)) {
        Add-Warning ".git/hooks not found. Skipping hook installation."
        return
    }

    $hookPath = Join-Path $hookDir "pre-commit"
    $script = @'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
powershell -NoProfile -ExecutionPolicy Bypass -File "$ROOT/sovereignty_audit.ps1" -VerifyHashes
'@
    Set-Content -Path $hookPath -Value $script
    Write-Host "Installed pre-commit hook: $hookPath"
}

function Resolve-HostIps {
    param([string]$HostName)
    try {
        $records = Resolve-DnsName -Name $HostName -Type A -ErrorAction Stop
        return ($records | Select-Object -ExpandProperty IPAddress -Unique)
    }
    catch {
        return @()
    }
}

function Apply-Lockdown {
    Write-Section "Network Lockdown"

    $policyRows = @()
    foreach ($host in $ForbiddenHosts) {
        $ips = Resolve-HostIps -HostName $host
        $policyRows += [PSCustomObject]@{
            host = $host
            ips = ($ips -join ",")
        }
    }
    $policyRows | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $ReportsDir "lockdown_hosts.json")
    Write-Host "Lockdown host map written to reports\sovereignty\lockdown_hosts.json"

    if (-not $ApplyFirewall) {
        Write-Host "Firewall changes not applied. Re-run with -Lockdown -ApplyFirewall to enforce."
        return
    }

    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).
        IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Add-Finding "Firewall enforcement requires Administrator privileges."
        return
    }

    foreach ($row in $policyRows) {
        if ([string]::IsNullOrWhiteSpace($row.ips)) {
            Add-Warning "No IPv4 addresses resolved for $($row.host). Skipping firewall rule."
            continue
        }
        $ruleName = "MoStar-Sov-Block-$($row.host)"
        Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
        New-NetFirewallRule -DisplayName $ruleName -Direction Outbound -Action Block -RemoteAddress $row.ips -Profile Any | Out-Null
        Write-Host "Applied firewall block: $ruleName -> $($row.ips)"
    }
}

Write-Section "MoStar Sovereignty Audit"
Run-DeepScan

if ($DependencyGraph) { Run-DependencyGraph }
if ($StaticAnalysis) { Run-StaticAnalysis }
if ($Clean) { Run-Clean }
if ($GenerateHashes) { Generate-HashLock }
if ($VerifyHashes) { Verify-HashLock }
if ($InstallHook) { Install-PreCommitHook }
if ($Lockdown) { Apply-Lockdown }

Write-Section "Summary"
Write-Host ("Findings: {0}" -f $Findings.Count)
Write-Host ("Warnings: {0}" -f $Warnings.Count)
Write-Host ("Reports: {0}" -f $ReportsDir)

if ($Findings.Count -gt 0 -and -not $NoFailOnFindings) {
    exit 1
}

exit 0
