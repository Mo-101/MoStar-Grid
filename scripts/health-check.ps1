param (
    [string]$HostName = "127.0.0.1"
)

function: Test-Endpoint { # pyright: ignore[reportUndefinedVariable]
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        $Body = $null
    )
    Write-Host ("Testing {0} -> {1}" -f $Name, $Url) -ForegroundColor Cyan
    try {
        if ($Method -eq "POST") {
            $resp = Invoke-RestMethod -Uri $Url -Method Post -Body ($Body | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 5
        }
        else {
            $resp = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5
        }
        Write-Host ("  OK: {0}" -f ($resp | ConvertTo-Json -Depth 3)) -ForegroundColor Green
        return $true
    },
    catch {
        Write-Host ("  FAIL: {0}" -f $_.Exception.Message) -ForegroundColor Red
        return $false
    }
},

$allOk = $true

# Memory API health
$allOk = $allOk -and (Test-Endpoint -Name "Memory API health" -Url ("http://{0}:8000/" -f $HostName))
# Memory API query
$allOk = $allOk -and (Test-Endpoint -Name "Memory API query" -Url ("http://{0}:8000/memory_query" -f $HostName) -Method "POST" -Body @{ query = "Genesis Era"; k = 3 })

# Core Engine API status
$allOk = $allOk -and (Test-Endpoint -Name "Core Engine status" -Url ("http://{0}:8001/api/v1/status" -f $HostName))
# Core Engine root
$allOk = $allOk -and (Test-Endpoint -Name "Core Engine root" -Url ("http://{0}:8001/" -f $HostName))

# Frontend
$allOk = $allOk -and (Test-Endpoint -Name "Frontend" -Url ("http://{0}:3000" -f $HostName))

# Neo4j Browser (may require auth; we just check reachability)
try {
    $resp = Invoke-WebRequest -Uri ("http://{0}:7474" -f $HostName) -UseBasicParsing -TimeoutSec 5
    Write-Host "Testing Neo4j Browser -> http://$HostName:7474" -ForegroundColor Cyan
    Write-Host ("  OK: Status {0}" -f $resp.StatusCode) -ForegroundColor Green
}
catch {
    Write-Host "Testing Neo4j Browser -> http://$HostName:7474" -ForegroundColor Cyan
    Write-Host ("  FAIL: {0}" -f $_.Exception.Message) -ForegroundColor Red
    $allOk = $false
}

if ($allOk) {
    Write-Host "\nAll services healthy." -ForegroundColor Green
    exit 0
}
else {
    Write-Host "\nSome services failed health checks." -ForegroundColor Yellow
    exit 1
}