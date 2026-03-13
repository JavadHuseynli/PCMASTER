@echo off
chcp 65001 >nul
title ClassRoom Manager - Agent Build
echo ========================================
echo   Yalniz Agent EXE yaradilir...
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [XETA] Python tapilmadi! Evvelce install.bat isledin.
    pause
    exit /b 1
)

cd /d "%~dp0\.."
pip install PyQt6 Pillow mss cryptography pyinstaller -q
python build_agent.py --onefile

echo.
echo Agent EXE: dist\ClassRoomAgent.exe
echo Bu faylI sagird komputerlerine kopyalayin.
echo.
pause
