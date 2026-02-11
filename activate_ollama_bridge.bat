@echo off
echo 🔥 MoStar Grid - Activating Ollama Cloud Bridge...
echo 🚇 Tunnel: mostar-ollama
echo 🌐 URL: https://ollama.mostarindustries.com
echo.
echo [CTRL+C] to deactivate the bridge.
echo.
C:\Tools\cloudflared.exe tunnel run mostar-ollama
pause
