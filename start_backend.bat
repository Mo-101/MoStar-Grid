@echo off
REM Start MoStar Grid Backend API Server
REM This starts the FastAPI server on port 8000

echo 🔥 Starting MoStar Grid Backend API...
echo.

REM Set environment variables
set NEO4J_URI=bolt://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=mostar123
set OLLAMA_MODEL=mostar-ai
set OLLAMA_HOST=http://localhost:11434
set TTS_LANG=en

echo Environment configured:
echo   - Neo4j: %NEO4J_URI%
echo   - Ollama: %OLLAMA_HOST%
echo   - Model: %OLLAMA_MODEL%
echo.

REM Try to start with uvicorn
echo Starting FastAPI server on port 8000...
cd backend
python -m uvicorn core_engine.api_gateway:app --host 0.0.0.0 --port 8000 --reload

REM If that fails, try with full path
if errorlevel 1 (
    echo.
    echo ⚠️ Default python not found, trying custom path...
    C:\Tools\python-3.15.0a3-embed-amd64\python.exe -m uvicorn core_engine.api_gateway:app --host 0.0.0.0 --port 8000 --reload
)

if errorlevel 1 (
    echo.
    echo ❌ Failed to start backend server
    echo.
    echo Please install dependencies:
    echo   pip install fastapi uvicorn neo4j python-dotenv httpx gtts
    echo.
    pause
)
