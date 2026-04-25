@echo off
echo ========================================
echo   Setup
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.11 and add it to PATH.
    pause
    exit /b 1
)

if exist "venv\" (
    echo [1/2] Virtual environment already exists, skipping creation.
) else (
    echo [1/2] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo       Done.
)

echo [2/2] Installing required packages...
call venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install packages.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup completed successfully!
echo ========================================
echo.
echo   To start the server:
echo     - double-click start_server.bat
echo     - or run: venv\Scripts\activate
echo               python server.py
echo.
pause