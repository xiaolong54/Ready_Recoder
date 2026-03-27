@echo off
chcp 65001 >nul
title Fix GUI Startup Issues
color 0A
echo.
echo ========================================
echo   SocialMediaCut GUI Fix Tool
echo ========================================
echo.

echo [1/5] Checking Python environment...
py --version
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)
echo OK: Python environment found
echo.

echo [2/5] Checking tkinter module...
py -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo Error: tkinter module not available
    echo.
    echo tkinter is required for Python GUI, but your Python installation may not include it.
    echo.
    echo ========================================
    echo   Solutions:
    echo ========================================
    echo.
    echo Solution A: Reinstall Python (Recommended)
    echo   1. Visit https://www.python.org/downloads/
    echo   2. Download Python 3.11.x Windows installer
    echo   3. During installation, make sure to check:
    echo      Add Python to PATH
    echo      tcl/tk and IDLE
    echo.
    echo Solution B: Install Microsoft Store Python
    echo   1. Open Microsoft Store
    echo   2. Search for "Python 3.11"
    echo   3. Install Python 3.11.x
    echo   4. This version includes tkinter
    echo.
    echo Solution C: Use CLI mode (No GUI)
    echo   If you don't want to reinstall, you can use command line mode:
    echo   Double click: 启动服务.bat
    echo   Or run: py main.py
    echo.
    pause
    exit /b 1
)
echo OK: tkinter module available
echo.

echo [3/5] Checking ttkbootstrap module...
py -c "import ttkbootstrap" >nul 2>&1
if errorlevel 1 (
    echo Error: ttkbootstrap module not installed
    echo Installing ttkbootstrap...
    py -m pip install ttkbootstrap
    if errorlevel 1 (
        echo Failed to install ttkbootstrap
        pause
        exit /b 1
    )
    echo OK: ttkbootstrap installed successfully
) else (
    echo OK: ttkbootstrap module available
)
echo.

echo [4/5] Checking other dependencies...
echo Checking required modules...
py -m pip show requests >nul 2>&1
if errorlevel 1 (
    echo Installing requests...
    py -m pip install requests
)
py -m pip show PyYAML >nul 2>&1
if errorlevel 1 (
    echo Installing PyYAML...
    py -m pip install PyYAML
)
echo OK: Dependencies checked
echo.

echo [5/5] Verifying GUI startup...
echo Attempting to start GUI...
echo.
py gui.py
if errorlevel 1 (
    echo.
    echo Error: GUI startup failed
    echo.
    echo Possible reasons:
    echo 1. tkinter version issues
    echo 2. Other dependencies missing
    echo 3. Code errors
    echo.
    echo Please check the error messages above
    pause
    exit /b 1
)
echo.

echo Success! GUI has started successfully
echo.
pause
