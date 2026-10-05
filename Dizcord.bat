@echo off
cd /d "%~dp0"
if not exist "%~dp0runtime\pythonw.exe" (
  echo First start: setting up the portable runtime...
  call "%~dp0setup.bat"
  if not exist "%~dp0runtime\pythonw.exe" exit /b 1
)
start "" "%~dp0runtime\pythonw.exe" "%~dp0main.py"
