@echo off
chcp 65001 >nul
echo ======================================
echo    PigBaby Mouse Automation Tool
echo ======================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.8+
    pause
    exit /b 1
)

REM Check virtual environment
if exist "venv\Scripts\python.exe" (
    echo [Info] Using virtual environment
    call venv\Scripts\activate.bat
) else (
    echo [Info] Using system Python
)

REM Check dependencies
echo [Info] Checking dependencies...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo [Warning] Dependencies not installed, installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [Error] Dependency installation failed
        pause
        exit /b 1
    )
)

echo [Info] Starting program...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo [Error] Program exited abnormally
    pause
)