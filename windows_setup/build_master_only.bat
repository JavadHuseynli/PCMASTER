@echo off
chcp 65001 >nul
title ClassRoom Manager - Master Build
echo ========================================
echo   Yalniz Master EXE yaradilir...
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
python build_agent.py --master --onefile

echo.
echo Master EXE: dist\ClassRoomMaster.exe
echo Bu fayli oz komputerinizde isledin.
echo.
pause
