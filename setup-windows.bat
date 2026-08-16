@echo off
REM ===========================================================================
REM  Trades Directory - one-time setup for Windows
REM
REM  Creates the database, loads the tables and the sample data, and installs
REM  the Python packages the application needs.
REM
REM  Run this ONCE, after installing PostgreSQL and Python.
REM  Double-click it, or run it from a Command Prompt in this folder.
REM ===========================================================================

chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  ============================================
echo   Trades Directory - setup
echo  ============================================
echo.

REM --- locate psql -----------------------------------------------------------
set "PSQL="
set "CREATEDB="

where psql >nul 2>&1
if %errorlevel%==0 (
    set "PSQL=psql"
    set "CREATEDB=createdb"
    goto :found_psql
)

for %%V in (18 17 16 15 14 13) do (
    if exist "C:\Program Files\PostgreSQL\%%V\bin\psql.exe" (
        set "PSQL=C:\Program Files\PostgreSQL\%%V\bin\psql.exe"
        set "CREATEDB=C:\Program Files\PostgreSQL\%%V\bin\createdb.exe"
        goto :found_psql
    )
)

echo  [X] Could not find psql.
echo.
echo      PostgreSQL does not appear to be installed, or it went to an
echo      unusual location. Install it from:
echo          https://www.postgresql.org/download/windows/
echo.
pause
exit /b 1

:found_psql
echo  [OK] Found psql: !PSQL!

REM --- check python ----------------------------------------------------------
where python >nul 2>&1
if not %errorlevel%==0 (
    echo  [X] Python is not on PATH.
    echo.
    echo      Re-run the Python installer, choose "Modify", and tick
    echo      "Add python.exe to PATH". Then run this script again.
    echo.
    pause
    exit /b 1
)
echo  [OK] Found Python
echo.

REM --- password --------------------------------------------------------------
echo  Enter the password you set for the PostgreSQL "postgres" user
echo  when you installed PostgreSQL.
echo.
set /p PGPW=  Password:
if "!PGPW!"=="" (
    echo.
    echo  [X] No password entered. Stopping.
    pause
    exit /b 1
)
set "PGPASSWORD=!PGPW!"

REM --- verify the password works before doing anything else -------------------
echo.
echo  Checking the connection...
"!PSQL!" -U postgres -d postgres -c "SELECT 1;" >nul 2>&1
if not %errorlevel%==0 (
    echo  [X] Could not connect. The password is probably wrong.
    echo      There is no way to recover it - if it is lost, reinstall
    echo      PostgreSQL and choose a new one.
    echo.
    pause
    exit /b 1
)
echo  [OK] Connected

REM --- create the database ---------------------------------------------------
echo.
echo  Creating the database...
"!CREATEDB!" -U postgres -E UTF8 trades_db 2>nul
if %errorlevel%==0 (
    echo  [OK] Created trades_db
) else (
    echo  [i]  trades_db already exists - reloading it from scratch
    "!PSQL!" -U postgres -d postgres -c "DROP DATABASE trades_db;" >nul 2>&1
    "!CREATEDB!" -U postgres -E UTF8 trades_db
    if not !errorlevel!==0 (
        echo  [X] Could not recreate the database. Close pgAdmin and any open
        echo      psql window, then run this again.
        pause
        exit /b 1
    )
    echo  [OK] Recreated trades_db
)

REM --- load structure and data -----------------------------------------------
echo.
echo  Loading tables...
"!PSQL!" -U postgres -d trades_db -q -f schema.sql
if not %errorlevel%==0 goto :load_failed

echo  Loading sample data...
"!PSQL!" -U postgres -d trades_db -q -f seed.sql
if not %errorlevel%==0 goto :load_failed

echo  [OK] Database loaded
goto :deps

:load_failed
echo  [X] Loading failed. The error above says which statement.
pause
exit /b 1

REM --- python packages -------------------------------------------------------
:deps
echo.
echo  Installing Python packages (this can take a minute)...
python -m pip install --quiet --disable-pip-version-check "fastapi[standard]" "psycopg[binary]" jinja2
if not %errorlevel%==0 (
    echo  [X] pip failed. If you are offline, connect and try again.
    pause
    exit /b 1
)
echo  [OK] Packages installed

REM --- remember the connection for run-windows.bat ----------------------------
> local-db.bat echo @echo off
>> local-db.bat echo set DATABASE_URL=dbname=trades_db user=postgres password=!PGPW! host=127.0.0.1 client_encoding='UTF8'

REM --- verify ----------------------------------------------------------------
echo.
echo  Checking the data...
"!PSQL!" -U postgres -d trades_db -t -c "SELECT 'trades=' || (SELECT count(*) FROM trade) || '  shops=' || (SELECT count(*) FROM shop) || '  branches=' || (SELECT count(*) FROM branch) || '  employees=' || (SELECT count(*) FROM employee);"

echo.
echo  ============================================
echo   Setup complete.
echo.
echo   Expected above: trades=7  shops=8
echo                   branches=13  employees=17
echo.
echo   Now double-click:  run-windows.bat
echo  ============================================
echo.
pause
