@echo off
setlocal
set "SCRIPT_DIR=%~dp0..\"

where py >nul 2>nul
if not errorlevel 1 goto run_py

where python >nul 2>nul
if not errorlevel 1 goto run_python

echo Python 3 was not found. Install Python 3 or edit scripts\windows\switch-to-channel-3.cmd.
exit /b 1

:run_py
py -3 "%SCRIPT_DIR%logi_switch.py" switch channel-3 %*
exit /b %ERRORLEVEL%

:run_python
python "%SCRIPT_DIR%logi_switch.py" switch channel-3 %*
exit /b %ERRORLEVEL%
