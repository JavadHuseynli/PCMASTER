@echo off
chcp 65001 >nul
title ClassRoom Manager - Qurasdirma

:: Python yoxla
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [XETA] Python tapilmadi!
    echo  Python yukleyin: https://www.python.org/downloads/
    echo  Qurasdirma zamani "Add Python to PATH" secin!
    echo.
    pause
    exit /b 1
)

:: Repo qovlugunu classroom_manager olaraq kopyala (import ucun lazimdir)
cd /d "%~dp0\.."
set "REPO_DIR=%cd%"
set "PARENT_DIR=%REPO_DIR%\.."
set "TARGET=%PARENT_DIR%\classroom_manager"

if not exist "%TARGET%\__init__.py" (
    echo Paket strukturu qurulur...
    if not "%~n1"=="classroom_manager" (
        xcopy "%REPO_DIR%" "%TARGET%\" /E /I /Y /Q >nul 2>&1
    )
)

:: GUI installer ac
python "%REPO_DIR%\installer.py"
