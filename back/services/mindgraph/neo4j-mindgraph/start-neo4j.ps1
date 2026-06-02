$env:JAVA_HOME = 'C:\Tools\jdk-21\jdk-21.0.5+11'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

Write-Host '=== NEO4J — MoStar Grid ===' -ForegroundColor Green

Set-Location -Path $PSScriptRoot
./bin/neo4j.bat console
