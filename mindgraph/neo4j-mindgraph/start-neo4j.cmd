@echo off
setlocal
cd /d "%~dp0"

REM Starts local Neo4j with the bundled JDK 21 (extracts it into .tools/ on first run).
REM If Docker's mostar-neo4j container is running, either stop it first or pass -StopDocker.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-neo4j.ps1" %*

echo.
echo Neo4j console exited.
pause

