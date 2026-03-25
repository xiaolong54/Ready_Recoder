@echo off
chcp 65001 >nul
title SocialMediaCut - GUI
echo Starting GUI...
set PYTHON_HOME=C:\Users\a1525\AppData\Local\Programs\Python\Python311
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%
cd /d %~dp0
python -c "import ttkbootstrap" >nul 2>nul
if errorlevel 1 (
  echo Missing dependency: ttkbootstrap
  echo Please run: pip install -r requirements.txt
  pause
  exit /b 1
)
python gui.py
