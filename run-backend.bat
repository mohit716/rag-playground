@echo off
REM Activates venv and runs the backend on port 8001
cd /d %~dp0
cd ..
cd ..
call .\.venv\Scripts\activate.bat
python -m uvicorn labs.rag_lab.app:app --reload --port 8001
