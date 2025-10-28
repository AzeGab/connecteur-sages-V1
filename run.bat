@echo off
REM Lancer le serveur de développement FastAPI
setlocal
if not exist "%~dp0venv\Scripts\activate.bat" (
  echo [INFO] Conseil: créez un venv et installez les deps: python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
)
uvicorn app.main:app --reload
endlocal

