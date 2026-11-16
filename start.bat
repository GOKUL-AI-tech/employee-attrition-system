@echo off
title Employee Attrition Prediction System
cd /d "%~dp0"

echo === Backend (Flask) ===
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
start "Attrition Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate.bat && python app.py"
cd ..

echo === Frontend (React) ===
cd frontend
if not exist node_modules (
    call npm install
)
start "" http://localhost:5173
call npm run dev
