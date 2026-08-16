<#
    Trades Directory - one-time setup (PowerShell)

    Creates the database, loads the tables and the sample data, and installs
    the Python packages the application needs.

    Run it once, after installing PostgreSQL and Python:

        powershell -ExecutionPolicy Bypass -File setup-windows.ps1

    Or just double-click setup-windows.bat, which does the same thing.
#>

$ErrorActionPreference = 'Stop'

# The console and psql must both be in UTF-8, or every Arabic row is rejected
# with "byte sequence ... in encoding WIN1252 has no equivalent in UTF8".
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PGCLIENTENCODING = 'UTF8'

Set-Location -Path $PSScriptRoot

function Say  { param($m) Write-Host "  $m" }
function Ok   { param($m) Write-Host "  [OK] $m"  -ForegroundColor Green }
function Info { param($m) Write-Host "  [i]  $m"  -ForegroundColor Yellow }
function Die  { param($m)
    Write-Host ""
    Write-Host "  [X] $m" -ForegroundColor Red
    Write-Host ""
    Read-Host "  Press Enter to close"
    exit 1
}

Write-Host ""
Write-Host "  ============================================"
Write-Host "   Trades Directory - setup"
Write-Host "  ============================================"
Write-Host ""

# --- are the project files here? --------------------------------------------
foreach ($f in 'schema.sql', 'seed.sql', 'app_starter.py') {
    if (-not (Test-Path $f)) {
        Write-Host "  [X] The project files are not in this folder." -ForegroundColor Red
        Write-Host ""
        Write-Host "      Looking in: $PSScriptRoot"
        Write-Host "      Missing:    $f"
        Write-Host ""
        Write-Host "      Download the whole project and run this from inside it:"
        Write-Host "        https://github.com/Mo7ammedMajdy/trades-directory"
        Write-Host "        Code > Download ZIP > extract > run this from the extracted folder"
        Write-Host ""
        Read-Host "  Press Enter to close"
        exit 1
    }
}
Ok "Project files found"

# --- locate the PostgreSQL tools --------------------------------------------
$pgBin = $null
if (Get-Command psql -ErrorAction SilentlyContinue) {
    $pgBin = Split-Path (Get-Command psql).Source
} else {
    foreach ($v in 18, 17, 16, 15, 14, 13) {
        $candidate = "C:\Program Files\PostgreSQL\$v\bin"
        if (Test-Path "$candidate\psql.exe") { $pgBin = $candidate; break }
    }
}
if (-not $pgBin) {
    Die @"
Could not find psql.

      PostgreSQL does not appear to be installed, or it went somewhere
      unusual. Install it from:
          https://www.postgresql.org/download/windows/
"@
}
# Putting the folder on PATH for this session means psql and createdb can be
# called by name for the rest of the script.
$env:Path = "$env:Path;$pgBin"
Ok "Found PostgreSQL tools: $pgBin"

# --- python ------------------------------------------------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Die @"
Python is not on PATH.

      Re-run the Python installer, choose "Modify", and tick
      "Add python.exe to PATH". Then run this script again.
"@
}
Ok "Found Python"

# --- password ----------------------------------------------------------------
Write-Host ""
Say "Enter the password you set for the PostgreSQL 'postgres' user"
Say "when you installed PostgreSQL."
Write-Host ""
$pw = Read-Host "  Password"
if ([string]::IsNullOrWhiteSpace($pw)) { Die "No password entered." }
$env:PGPASSWORD = $pw

# --- check it before touching anything ---------------------------------------
Write-Host ""
Say "Checking the connection..."
psql -U postgres -d postgres -c "SELECT 1;" *> $null
if ($LASTEXITCODE -ne 0) {
    Die @"
Could not connect. The password is probably wrong.

      There is no way to recover it. If it is lost, reinstall PostgreSQL
      and choose a new one.
"@
}
Ok "Connected"

# --- create the database -----------------------------------------------------
Write-Host ""
Say "Creating the database..."
$exists = (psql -U postgres -d postgres -t -A -c "SELECT 1 FROM pg_database WHERE datname='trades_db';")
if ($exists -eq '1') {
    Info "trades_db already exists - rebuilding it from scratch"
    psql -U postgres -d postgres -c "DROP DATABASE trades_db;" *> $null
    if ($LASTEXITCODE -ne 0) {
        Die "Could not drop trades_db. Close pgAdmin and any open psql window, then run this again."
    }
}
createdb -U postgres -E UTF8 trades_db
if ($LASTEXITCODE -ne 0) { Die "Could not create the database." }
Ok "trades_db created"

# --- load --------------------------------------------------------------------
# ON_ERROR_STOP matters: without it psql exits 0 even when statements fail,
# and setup reports success over a half-loaded database.
Write-Host ""
Say "Loading tables..."
psql -U postgres -d trades_db -q -v ON_ERROR_STOP=1 -f schema.sql
if ($LASTEXITCODE -ne 0) { Die "schema.sql failed. The error above says which statement." }

Say "Loading sample data..."
psql -U postgres -d trades_db -q -v ON_ERROR_STOP=1 -f seed.sql
if ($LASTEXITCODE -ne 0) { Die "seed.sql failed. The error above says which statement." }
Ok "Database loaded"

# --- verify, do not assume ---------------------------------------------------
Write-Host ""
Say "Checking the data..."
$shops     = [int](psql -U postgres -d trades_db -t -A -c "SELECT count(*) FROM shop;")
$branches  = [int](psql -U postgres -d trades_db -t -A -c "SELECT count(*) FROM branch;")
$employees = [int](psql -U postgres -d trades_db -t -A -c "SELECT count(*) FROM employee;")
$trades    = [int](psql -U postgres -d trades_db -t -A -c "SELECT count(*) FROM trade;")
Say "trades=$trades  shops=$shops  branches=$branches  employees=$employees"

if ($shops -ne 8 -or $branches -ne 13 -or $employees -ne 17 -or $trades -ne 7) {
    Die @"
The data did not load correctly.
      Expected trades=7 shops=8 branches=13 employees=17.

      If the errors above mention WIN1252 or encoding, the console is not
      in UTF-8. Use Windows Terminal rather than the old Command Prompt.
"@
}
Ok "Data verified"

# --- python packages ---------------------------------------------------------
Write-Host ""
Say "Installing Python packages (this can take a minute)..."
python -m pip install --quiet --disable-pip-version-check "fastapi[standard]" "psycopg[binary]" jinja2
if ($LASTEXITCODE -ne 0) { Die "pip failed. If you are offline, connect and try again." }
Ok "Packages installed"

# --- remember the connection for run-windows.ps1 -----------------------------
# This file holds the password, so it is gitignored and stays on this machine.
"`$env:DATABASE_URL = `"dbname=trades_db user=postgres password=$pw host=127.0.0.1 client_encoding='UTF8'`"" |
    Set-Content -Path (Join-Path $PSScriptRoot 'local-db.ps1') -Encoding UTF8

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Green
Write-Host "   Setup complete." -ForegroundColor Green
Write-Host ""
Write-Host "   trades=7  shops=8  branches=13  employees=17"
Write-Host ""
Write-Host "   Now run:  .\run-windows.ps1"
Write-Host "   (or double-click run-windows.bat)"
Write-Host "  ============================================" -ForegroundColor Green
Write-Host ""
Read-Host "  Press Enter to close"
