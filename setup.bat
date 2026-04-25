@echo off
chcp 65001 >nul
echo ========================================
echo   Установка окружение
echo ========================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите Python 3.11 и добавьте его в PATH.
    pause
    exit /b 1
)

:: Шаг 1: Создание виртуального окружения (если его нет)
if exist "venv\" (
    echo [1/2] Виртуальное окружение уже существует, пропускаем создание.
) else (
    echo [1/2] Создание виртуального окружения Python...
    python -m venv venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение.
        pause
        exit /b 1
    )
    echo       Готово.
)

:: Шаг 2: Установка библиотек
echo [2/2] Установка необходимых библиотек...
call venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить библиотеки.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Установка успешно завершена!
echo ========================================
echo.
echo   Для запуска сервера:
echo     - дважды кликните start_server.bat
echo     - или выполните: venv\Scripts\activate
echo                      python server.py
echo.
pause