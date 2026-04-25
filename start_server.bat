@echo off
chcp 65001 >nul
echo ========================================
echo Запуск Сервера
echo ========================================
echo.
echo Сервер запущен. Не закрывайте это окно.
echo Для остановки нажмите Ctrl+C.
echo.
call venv\Scripts\activate
python server.py
pause