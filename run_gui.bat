@echo off
set PYTHON_HOME=C:\Users\a1525\AppData\Local\Programs\Python\Python311
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%
cd /d %~dp0
python gui.py
pause
