@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: Üst qovluqda classroom_manager yoxdursa, yarad
if not exist "..\classroom_manager\__init__.py" (
    mkdir "..\classroom_manager" 2>nul
    xcopy "%cd%" "..\classroom_manager\" /E /I /Y /Q >nul 2>&1
)

python run_agent.py
if %errorlevel% neq 0 (
    echo.
    echo XETA: Python ve ya asililiqlar tapilmadi.
    echo Evvelce install.bat isledin.
    pause
)
