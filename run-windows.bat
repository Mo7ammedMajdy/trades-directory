@echo off
REM ===========================================================================
REM  Trades Directory - start the application
REM
REM  Double-click this file. Run setup-windows.bat once first.
REM  Leave the window open while using the site; Ctrl+C stops it.
REM ===========================================================================

cd /d "%~dp0"

if not exist "run-windows.ps1" (
    echo.
    echo  [X] run-windows.ps1 is missing from this folder:
    echo        %CD%
    echo.
    echo      Download the whole project, not individual files.
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-windows.ps1"
