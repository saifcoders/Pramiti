@echo off
cd /d "%~dp0backend"
if exist "%~dp0backend\venv\Scripts\uvicorn.exe" (
    "%~dp0backend\venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000
) else (
    uvicorn app.main:app --host 0.0.0.0 --port 8000
)
