@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3-64 -m pip install --upgrade pywin32
) else (
  python -m pip install --upgrade pywin32
)
if errorlevel 1 (
  echo Installation failed.
  echo Press any key to continue . . .
  pause >nul
  exit /b 1
)
echo pywin32 installation complete.
echo Press any key to continue . . .
pause >nul
