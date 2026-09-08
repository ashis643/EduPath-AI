@echo off
title EduPath AI Web Application Launcher
echo ===================================================
echo   EduPath AI — Starting Web Application...
echo ===================================================
echo.
cd /d "%~dp0"

echo [1/2] Seeding Database...
python database\seed_data.py

echo.
echo [2/2] Launching Web Application Server on http://127.0.0.1:5000 ...
start "" "http://127.0.0.1:5000"
python app.py
pause
