@echo off
chcp 65001 >nul
echo ====================================
echo   GitHub 上传脚本
echo ====================================
echo.
python git_manager.py
echo.
pause
