@echo off
chcp 65001 >nul
title 抖音直播录像工具
echo 正在启动...
set PYTHON_HOME=C:\Users\a1525\AppData\Local\Programs\Python\Python311
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%
cd /d %~dp0
python main.py
pause
