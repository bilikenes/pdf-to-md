@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Ilk kurulum yapiliyor...
    python -m venv .venv
    if errorlevel 1 goto :error
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

start "" ".venv\Scripts\pythonw.exe" app.py
exit /b 0

:error
echo.
echo Kurulum basarisiz oldu. Python 3.10 veya daha yenisinin kurulu oldugunu kontrol edin.
pause
exit /b 1
