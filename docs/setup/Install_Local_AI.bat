@echo off
rem  Sets up the AI model for the Minisceongo Creek walk-through on this Windows computer:
rem  https://faisal-b-ashraf.github.io/minisceongo-creek-erosion/
rem
rem  1. Installs Ollama, the free, open-source program that runs AI models on your own computer
rem     (from ollama.com, about 1 GB, no administrator rights needed), or updates it if it is too old.
rem  2. Lets that one web site talk to Ollama (sets OLLAMA_ORIGINS for your Windows account).
rem  3. Restarts Ollama. The web page then downloads the model and connects by itself.
rem
rem  Nothing else is changed. Safe to run again: it skips what is already done.
rem  To undo: uninstall Ollama in Windows Settings, Apps, then run
rem      reg delete HKCU\Environment /v OLLAMA_ORIGINS /f

setlocal EnableExtensions EnableDelayedExpansion
title Minisceongo Creek walk-through - AI setup
set "SITE=https://faisal-b-ashraf.github.io"
set "PAGE=https://faisal-b-ashraf.github.io/minisceongo-creek-erosion/"
set "NEED=0.17.1"
set "DIR=%LOCALAPPDATA%\Programs\Ollama"
set "API=http://127.0.0.1:11434/api/version"

echo.
echo  Setting up the AI for the Minisceongo Creek walk-through. Keep this window open.
echo.

rem ---- 1. Ollama: install it, or update it if it is older than the model needs
call :find
if defined EXE call :version
if defined EXE if "!OLD!"=="0" (
  echo  [1/3] Ollama !VER! is already installed.
  goto allow
)
if defined EXE (
  echo  [1/3] Updating Ollama !VER! to the latest version, about 1 GB. This takes a few minutes...
) else (
  echo  [1/3] Installing Ollama, about 1 GB. This takes a few minutes...
)
taskkill /f /im "ollama app.exe" >nul 2>nul
taskkill /f /im ollama.exe >nul 2>nul
set "SETUP=%TEMP%\OllamaSetup.exe"
curl.exe -L --fail --progress-bar -o "%SETUP%" "https://ollama.com/download/OllamaSetup.exe"
if not errorlevel 1 "%SETUP%" /SILENT /SUPPRESSMSGBOXES /NORESTART /SP-
del "%SETUP%" >nul 2>nul
call :find
if defined EXE call :version
if defined EXE if "!OLD!"=="0" (
  echo  [1/3] Ollama !VER! is installed.
  goto allow
)
echo  The direct download did not work; trying the Windows package manager instead...
winget install --id Ollama.Ollama --exact --silent --accept-package-agreements --accept-source-agreements
call :find
if not defined EXE goto failed
call :version
if "!OLD!"=="1" echo  Ollama !VER! is older than the model needs, which is %NEED% or newer. Update it from https://ollama.com/download
echo  [1/3] Ollama is installed.

rem ---- 2. Let the walk-through's web site use Ollama (keep any sites already allowed)
:allow
set "CUR="
for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v OLLAMA_ORIGINS 2^>nul ^| find /i "OLLAMA_ORIGINS"') do set "CUR=%%b"
set "NEW=%SITE%"
if not defined CUR goto setorigins
set "NEW=%CUR%,%SITE%"
echo %CUR% | find /i "%SITE%" >nul && set "NEW=%CUR%"
:setorigins
setx OLLAMA_ORIGINS "%NEW%" >nul
set "OLLAMA_ORIGINS=%NEW%"
echo  [2/3] %SITE% may now use Ollama.

rem ---- 3. Restart Ollama so it picks up the setting, then wait until it answers
taskkill /f /im "ollama app.exe" >nul 2>nul
taskkill /f /im ollama.exe >nul 2>nul
ping -n 2 127.0.0.1 >nul
if exist "%DIR%\ollama app.exe" (
  start "" "%DIR%\ollama app.exe"
) else (
  start "Ollama - close this window to stop it" /min "%EXE%" serve
)
set /a N=0
:wait
curl.exe -s -o nul "%API%" && goto ready
set /a N+=1
if %N% geq 60 goto notstarted
ping -n 2 127.0.0.1 >nul
goto wait

:ready
echo  [3/3] Ollama is running.
echo.
echo  Done. Go back to the web page: it finds Ollama by itself and asks before downloading the model.
echo  %PAGE%
echo.
pause
exit /b 0

:notstarted
echo.
echo  Ollama is installed but did not start. Start "Ollama" from the Start menu,
echo  then go back to the web page.
echo.
pause
exit /b 1

:failed
echo.
echo  Could not install Ollama automatically. Install it from https://ollama.com/download
echo  and then run this file again: it will skip the install and only do steps 2 and 3.
echo.
pause
exit /b 1

rem ---- helpers
:find
set "EXE="
if exist "%DIR%\ollama.exe" set "EXE=%DIR%\ollama.exe"
if not defined EXE for /f "delims=" %%p in ('where ollama.exe 2^>nul') do if not defined EXE set "EXE=%%p"
exit /b 0

:version
rem "ollama --version" ends its last line with the version number, e.g. "ollama version is 0.17.1"
set "VER=" & set "LINE=" & set "V=" & set "OLD=1"
for /f "delims=" %%L in ('call "%EXE%" --version 2^>^&1') do set "LINE=%%L"
for %%W in (!LINE!) do set "VER=%%W"
for /f "tokens=1-3 delims=.-" %%a in ("!VER!") do set /a "V=%%a*1000000+%%b*1000+%%c" >nul 2>nul
for /f "tokens=1-3 delims=.-" %%a in ("%NEED%") do set /a "W=%%a*1000000+%%b*1000+%%c"
if defined V if !V! geq !W! set "OLD=0"
exit /b 0
