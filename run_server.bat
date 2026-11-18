@echo off
setlocal

:: Determine script directory
set "SCRIPT_DIR=%~dp0"

:: 1. Check default ArcGIS Pro Python environment
set "PRO_PYTHON=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
if exist "%PRO_PYTHON%" (
    goto :RUN_SERVER
)

:: 2. Check propy.bat
set "PROPY_BAT=C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"
if exist "%PROPY_BAT%" (
    "%PROPY_BAT%" "%SCRIPT_DIR%run_server.py" %*
    goto :EOF
)

:: 3. Fallback to python on PATH
set "PRO_PYTHON=python.exe"

:RUN_SERVER
"%PRO_PYTHON%" "%SCRIPT_DIR%run_server.py" %*

endlocal
