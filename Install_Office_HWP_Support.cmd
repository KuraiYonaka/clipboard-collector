@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3-64 -m pip install --upgrade pywin32 Pillow
) else (
  python -m pip install --upgrade pywin32 Pillow
)
if errorlevel 1 (
  echo Installation failed.
  echo Press any key to continue . . .
  pause >nul
  exit /b 1
)
echo Office and picture dependencies installed.
echo Press any key to continue . . .
pause >nul
