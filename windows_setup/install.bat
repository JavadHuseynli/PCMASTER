@echo off
chcp 65001 >nul
title ClassRoom Manager - Qurasdirma
echo ========================================
echo   ClassRoom Manager - Windows Qurasdirma
echo ========================================
echo.

:: Python yoxla
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [XETA] Python tapilmadi!
    echo Python yukleyin: https://www.python.org/downloads/
    echo Qurasdirma zamani "Add Python to PATH" secin!
    echo.
    pause
    exit /b 1
)

echo [OK] Python tapildi
python --version
echo.

:: Asililiqlar yukle
echo Asililiqlar yuklenir...
pip install PyQt6>=6.5.0 Pillow>=10.0.0 mss>=9.0.0 cryptography>=41.0.0 pyinstaller
echo.

:: Agent build
echo ========================================
echo   Agent EXE yaradilir...
echo ========================================
cd /d "%~dp0\.."
python build_agent.py --onefile

echo.
echo ========================================
echo   Master EXE yaradilir...
echo ========================================
python build_agent.py --master --onefile

echo.
echo ========================================
echo   TAMAMDIR!
echo ========================================
echo.
echo Fayllar:
echo   dist\ClassRoomAgent.exe  - Sagird komputerleri ucun
echo   dist\ClassRoomMaster.exe - Muellim komputeri ucun
echo.
echo ClassRoomAgent.exe-ni her sagird komputerine kopyalayin.
echo ClassRoomMaster.exe-ni oz komputerinizde acin.
echo.
pause
