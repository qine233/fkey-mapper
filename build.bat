@echo off
chcp 65001 >nul
echo ============================================
echo   FKey Mapper - Build Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller
echo.

REM Build exe
echo [2/3] Building executable...
pyinstaller --onefile --windowed --uac-admin --hidden-import keyboard --name FKeyMapper main.py
echo.

REM Done
echo [3/3] Done!
echo Output: dist\FKeyMapper.exe
echo.
echo NOTE: The exe will request administrator privileges on first run.
echo       This is required for keyboard hook functionality.
pause
