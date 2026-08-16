@echo off
REM ===========================================================================
REM  Trades Directory - start the application
REM
REM  Run setup-windows.bat once first. After that, double-click this file
REM  whenever you want the site running.
REM
REM  Leave this window open while using the site. Close it, or press Ctrl+C,
REM  to stop the server.
REM ===========================================================================

chcp 65001 >nul
cd /d "%~dp0"

if not exist local-db.bat (
    echo.
    echo  [X] Not set up yet.
    echo.
    echo      Run setup-windows.bat first - it creates the database and
    echo      saves the connection details.
    echo.
    pause
    exit /b 1
)

call local-db.bat

echo.
echo  ============================================
echo   Trades Directory
echo.
echo   Open this in your browser:
echo       http://127.0.0.1:8000
echo.
echo   Keep this window open while using the site.
echo   Press Ctrl+C here to stop it.
echo  ============================================
echo.

start "" http://127.0.0.1:8000
python -m fastapi run app_starter.py --port 8000

echo.
echo  Server stopped.
pause
