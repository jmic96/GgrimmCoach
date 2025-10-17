@echo off
title GgrimmCoach Server Launcher
setlocal enabledelayedexpansion

:: -----------------------------------------
:: CONFIG
:: -----------------------------------------
set PORT=8765
set NODE_PORT=11434
set OPENAI_API_KEY=sk-REPLACE_WITH_YOUR_KEY

:: -----------------------------------------
:: ENVIRONMENT SETUP
:: -----------------------------------------
if not exist ".venv" (
    echo [SETUP] Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate

echo [SETUP] Installing required Python packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: -----------------------------------------
:: BUILD PACKS AND USAGE
:: -----------------------------------------
echo [BUILD] Generating datasets and legality packs...
python -m tools.build_packs || (
    echo [ERROR] build_packs failed. & pause & exit /b 1
)
python -m tools.build_usage || (
    echo [ERROR] build_usage failed. & pause & exit /b 1
)
python -m tools.verify_all || (
    echo [ERROR] verify_all failed. & pause & exit /b 1
)

:: -----------------------------------------
:: START DAMAGE CALC SERVICE
:: -----------------------------------------
echo [NODE] Starting calc_service...
start "Damage Calc Service" cmd /c "cd calc_service && npm install && node calc_service.js"

:: -----------------------------------------
:: START MAIN PYTHON SERVER
:: -----------------------------------------
echo [PYTHON] Launching GgrimmCoach server on port %PORT% ...
python server.py

endlocal