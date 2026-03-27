@echo off
chcp 65001 >nul
title Verify GUI Fix
echo.
echo ========================================
echo   GUI Fix Verification
echo ========================================
echo.

echo [1] Checking Python...
py --version >nul 2>nul
if errorlevel 1 (
    echo X Python not found
    goto :error
)
echo OK Python available

echo [2] Checking tkinter...
py -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo X tkinter not available
    goto :error
)
echo OK tkinter available

echo [3] Checking ttkbootstrap...
py -c "import ttkbootstrap" >nul 2>nul
if errorlevel 1 (
    echo X ttkbootstrap not available
    goto :warning
)
echo OK ttkbootstrap available

echo [4] Checking platforms module...
py -c "from platforms import PlatformRegistry" >nul 2>nul
if errorlevel 1 (
    echo X platforms module error
    goto :error
)
echo OK platforms module works

echo [5] Checking app_core module...
py -c "from app_core import LiveRecorderApp" >nul 2>nul
if errorlevel 1 (
    echo X app_core module error
    goto :error
)
echo OK app_core module works

echo [6] Checking gui.py syntax...
py -m py_compile gui.py >nul 2>nul
if errorlevel 1 (
    echo X gui.py has syntax errors
    goto :error
)
echo OK gui.py syntax is correct

echo.
echo ========================================
echo   All Checks Passed!
echo ========================================
echo.
echo You can now start GUI by double-clicking:
echo   - 启动GUI.bat (Start GUI)
echo.
echo Or run from command line:
echo   py gui.py
echo.
goto :end

:warning
echo.
echo ========================================
echo   Warning
echo ========================================
echo.
echo Some dependencies are missing.
echo Please run:
echo   py -m pip install -r requirements.txt
echo.
goto :end

:error
echo.
echo ========================================
echo   Error
echo ========================================
echo.
echo GUI cannot be started due to errors above.
echo Please run:
echo   修复GUI.bat (Fix GUI)
echo.

:end
pause
