@echo off
chcp 65001 >nul
title ClassRoom Manager - Qurasdirma

:: Python yoxla
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [XETA] Python tapilmadi!
    echo.
    echo  Python yukleyin: https://www.python.org/downloads/
    echo  Qurasdirma zamani "Add Python to PATH" secin!
    echo.
    pause
    exit /b 1
)

:: GUI installer ac
cd /d "%~dp0\.."
python installer.py
