@echo off
setlocal
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
  start "" pyw -3-64 "%~dp0collector.pyw"
  exit /b 0
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "%~dp0collector.pyw"
  exit /b 0
)
echo Python 3 x64 not found.
echo Press any key to continue . . .
pause >nul
exit /b 1
