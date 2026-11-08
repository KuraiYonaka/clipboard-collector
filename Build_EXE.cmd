@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3-64") else (set "PY=python")
%PY% -m pip install --upgrade pyinstaller pywin32
if errorlevel 1 goto error
%PY% -m PyInstaller --onedir --windowed --clean --name "Clipboard Collector" --hidden-import pythoncom --hidden-import win32com.client collector.pyw
if errorlevel 1 goto error
echo.
echo Created: %~dp0dist\Clipboard Collector\Clipboard Collector.exe
echo Press any key to continue . . .
pause >nul
exit /b 0
:error
echo Build failed.
echo Press any key to continue . . .
pause >nul
exit /b 1
