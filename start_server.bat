@echo off
echo ========================================
echo   Server
echo ========================================
echo.
call venv\Scripts\activate
echo Server is running. Do not close this window.
echo Press Ctrl+C to stop.
echo.
python server.py
pause