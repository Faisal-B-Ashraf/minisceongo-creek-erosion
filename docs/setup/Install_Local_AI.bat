@echo off
rem  Sets up the AI model for the Minisceongo Creek walk-through on this Windows computer:
rem  https://faisal-b-ashraf.github.io/minisceongo-creek-erosion/
rem
rem  1. Lets that one web site talk to Ollama (sets OLLAMA_ORIGINS for your Windows account).
rem  2. Installs Ollama, the free, open-source program that runs AI models on your own computer
rem     (from ollama.com, about 1 GB, no administrator rights needed), or updates it if it is too old.
rem  3. Makes sure Ollama is running with that setting. The web page then downloads the model by itself.
rem
rem  Nothing else is changed. Safe to run again: it skips what is already done.
rem  To undo: uninstall Ollama in Windows Settings, Apps, then run
rem      reg delete HKCU\Environment /v OLLAMA_ORIGINS /f

setlocal EnableExtensions EnableDelayedExpansion
title Minisceongo Creek walk-through - AI setup
set "SITE=https://faisal-b-ashraf.github.io"
set "NEED=0.17.1"
set "DIR=%LOCALAPPDATA%\Programs\Ollama"
set "API=http://127.0.0.1:11434/api/version"

echo.
echo  Setting up the AI for the Minisceongo Creek walk-through.
echo  Keep this window open until it says Done. If an Ollama window pops up, you can close it.
echo.

rem ---- 1. Allow the web site first, so the Ollama that the installer starts already has the setting
set "CUR="
for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v OLLAMA_ORIGINS 2^>nul ^| find /i "OLLAMA_ORIGINS"') do set "CUR=%%b"
set "NEW=%SITE%"
if not defined CUR goto setorigins
set "NEW=%CUR%,%SITE%"
echo %CUR% | find /i "%SITE%" >nul && set "NEW=%CUR%"
:setorigins
setx OLLAMA_ORIGINS "%NEW%" >nul
set "OLLAMA_ORIGINS=%NEW%"
echo  [1/3] %SITE% may use Ollama.

rem ---- 2. Install Ollama, or update it if it is older than the model needs
call :find
if defined EXE call :version
if defined EXE if "!OLD!"=="0" (
  echo  [2/3] Ollama !VER! is already installed.
  goto run
)
if defined EXE (
  echo  [2/3] Updating Ollama !VER!, about 1 GB. This takes a few minutes...
) else (
  echo  [2/3] Installing Ollama, about 1 GB. This takes a few minutes...
)
call :stop
set "SETUP=%TEMP%\OllamaSetup.exe"
curl.exe -L --fail --progress-bar -o "%SETUP%" "https://ollama.com/download/OllamaSetup.exe"
if not errorlevel 1 "%SETUP%" /SILENT /SUPPRESSMSGBOXES /NORESTART /SP-
del "%SETUP%" >nul 2>nul
call :find
if defined EXE call :version
if defined EXE if "!OLD!"=="0" (
  echo  [2/3] Ollama !VER! is installed.
  goto run
)
echo  The direct download did not work; trying the Windows package manager instead...
winget install --id Ollama.Ollama --exact --silent --accept-package-agreements --accept-source-agreements
call :find
if not defined EXE goto failed
call :version
if "!OLD!"=="1" echo  Ollama !VER! is older than the model needs, which is %NEED% or newer. Update it from https://ollama.com/download
echo  [2/3] Ollama is installed.

rem ---- 3. Make sure Ollama is running and lets the site in. It is restarted only if it was
rem         running from before step 1 (only a fresh start picks up the setting) or if it is
rem         stuck: open, but not answering.
:run
echo  [3/3] Starting Ollama. The first start can take a minute or two...
set /a N=0
:check
call :allowed
if "!OK!"=="1" goto ready
call :running
if "!UP!"=="1" if not defined RESTARTED (
  set "RESTARTED=1"
  call :stop
  call :launch
)
if "!UP!"=="0" if !N! equ 5 (
  call :stop
  call :launch
)
if "!UP!"=="0" if !N! equ 45 (
  call :stop
  call :launch
)
set /a N+=1
if !N! geq 90 goto notstarted
if !N! equ 30 echo  Still starting...
if !N! equ 60 echo  Still starting. The first start can be slow while Windows checks the new program...
ping -n 3 127.0.0.1 >nul
goto check

:ready
echo  [3/3] Ollama is running.
echo.
echo  Done. Go back to the web page: it carries on by itself.
echo  You can close this window, and the Ollama window if one opened. Ollama keeps running in the background.
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
echo  and then run this file again: it will skip the install.
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

:allowed
rem Ollama answers with this header only for sites it allows
set "OK=0"
curl.exe -s -i -m 5 -H "Origin: %SITE%" "%API%" 2>nul | find /i "Access-Control-Allow-Origin" >nul && set "OK=1"
exit /b 0

:running
set "UP=0"
curl.exe -s -o nul -m 5 "%API%" && set "UP=1"
exit /b 0

:stop
rem ask Ollama to close, then make sure it has, and wait until its port is free
taskkill /im "ollama app.exe" >nul 2>nul
ping -n 3 127.0.0.1 >nul
taskkill /f /im "ollama app.exe" >nul 2>nul
taskkill /f /im ollama.exe >nul 2>nul
for /l %%i in (1,1,10) do (
  call :running
  if "!UP!"=="0" exit /b 0
  ping -n 3 127.0.0.1 >nul
)
exit /b 0

:launch
if exist "%DIR%\ollama app.exe" (
  start "" "%DIR%\ollama app.exe"
) else (
  start "Ollama - close this window to stop it" /min "%EXE%" serve
)
exit /b 0
