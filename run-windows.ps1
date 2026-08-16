<#
    Trades Directory - start the application (PowerShell)

        powershell -ExecutionPolicy Bypass -File run-windows.ps1

    Or double-click run-windows.bat.

    Leave the window open while using the site. Ctrl+C stops the server.
#>

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PGCLIENTENCODING = 'UTF8'

Set-Location -Path $PSScriptRoot

$config = Join-Path $PSScriptRoot 'local-db.ps1'
if (-not (Test-Path $config)) {
    Write-Host ""
    Write-Host "  [X] Not set up yet." -ForegroundColor Red
    Write-Host ""
    Write-Host "      Run setup-windows.ps1 first - it creates the database and"
    Write-Host "      saves the connection details."
    Write-Host ""
    Read-Host "  Press Enter to close"
    exit 1
}

. $config

Write-Host ""
Write-Host "  ============================================"
Write-Host "   Trades Directory"
Write-Host ""
Write-Host "   Open this in your browser:"
Write-Host "       http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Keep this window open while using the site."
Write-Host "   Press Ctrl+C to stop it."
Write-Host "  ============================================"
Write-Host ""

Start-Process "http://127.0.0.1:8000"
python -m fastapi run app_starter.py --port 8000

Write-Host ""
Write-Host "  Server stopped."
Read-Host "  Press Enter to close"
