@echo off
chcp 65001 >nul
title SocialMediaCut - GUI
echo Starting GUI...

REM Change to script directory
cd /d %~dp0

REM Check Python
echo Checking Python...
py --version >nul 2>nul
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

REM Check tkinter
echo Checking tkinter...
py -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo Error: tkinter module not available
    echo Your Python installation does not include tkinter
    echo Please reinstall Python with tcl/tk option
    pause
    exit /b 1
)

REM Check ttkbootstrap
echo Checking ttkbootstrap...
py -c "import ttkbootstrap" >nul 2>nul
if errorlevel 1 (
    echo Missing dependency: ttkbootstrap
    echo Please run: py -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting GUI...
py gui.py

if errorlevel 1 (
    echo.
    echo GUI startup failed
    pause
)
