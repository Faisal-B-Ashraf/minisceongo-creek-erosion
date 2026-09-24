@echo off
rem Opens the walk-through and project assistant in your browser.
rem Keep this window open while you use it; close it to stop.
cd /d "%~dp0"
python -c "import sys; sys.exit(sys.version_info[0] != 3)" >nul 2>nul
if not errorlevel 1 ( python serve_locally.py %* & goto :eof )
py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 ( py -3 serve_locally.py %* & goto :eof )
set "ARCPY=%ProgramFiles%\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
if exist "%ARCPY%" ( "%ARCPY%" serve_locally.py %* & goto :eof )
echo Python not found - using Windows PowerShell instead.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve_locally.ps1" %*
