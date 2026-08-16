@echo off
REM ===========================================================================
REM  Trades Directory - one-time setup
REM
REM  Double-click this file. It runs setup-windows.ps1, which does the work.
REM
REM  -ExecutionPolicy Bypass is needed because Windows blocks .ps1 files by
REM  default. It applies to this one run only and changes nothing on the
REM  machine.
REM ===========================================================================

cd /d "%~dp0"

if not exist "setup-windows.ps1" (
    echo.
    echo  [X] setup-windows.ps1 is missing from this folder:
    echo        %CD%
    echo.
    echo      Download the whole project, not individual files:
    echo        https://github.com/Mo7ammedMajdy/trades-directory
    echo        Code ^> Download ZIP ^> extract ^> run this from inside
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1"
