@echo off
echo ========================================================
echo   Bio-Entropic Market Analysis Framework - Setup
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment (.venv)...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/3] Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Installing Playwright Chromium browser binaries...
playwright install chromium

echo.
echo ========================================================
echo   Installation completed successfully!
echo   To run diagnostics:  python demo.py
echo   To start collection: python main.py
echo ========================================================
echo.
pause
