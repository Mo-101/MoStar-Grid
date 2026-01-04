@echo off
echo ============================================================
echo IKO IKANG - Voice of Flame API
echo ============================================================
echo.

cd /d "C:\Users\AI\Documents\MoStar\Mo Docs"

echo Installing dependencies...
pip install flask flask-cors neo4j --break-system-packages --quiet

echo.
echo Starting Flask API...
echo.

python ibibio_tts_api.py

pause
