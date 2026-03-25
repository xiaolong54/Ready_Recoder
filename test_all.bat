@echo off
chcp 65001 >nul
set PYTHON_HOME=C:\Users\a1525\AppData\Local\Programs\Python\Python311
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%
cd /d %~dp0

echo [1/3] Running syntax checks...
for %%f in (*.py) do (
  python -m py_compile "%%f"
  if errorlevel 1 goto :fail
)
python -m py_compile tests\test_room_manager.py tests\test_platform_parser.py tests\test_target_resolver.py tests\test_recorder_core.py tests\test_api_server.py tests\test_gui_state.py
if errorlevel 1 goto :fail

echo [2/3] Running unit tests...
python -m pytest -q
if errorlevel 1 goto :fail

echo [3/3] All checks passed.
exit /b 0

:fail
echo Tests failed.
exit /b 1
