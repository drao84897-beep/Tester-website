@echo off
cd /d "%~dp0"
echo ===================================================
echo Starting WebVerify AI - Website Authenticity Analyzer
echo ===================================================
call venv\Scripts\activate.bat
python app.py
pause
