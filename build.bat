@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Once run.bat ile kurulumu tamamlayin.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 goto :error

".venv\Scripts\pyinstaller.exe" --noconfirm --clean --windowed --onedir --name "PDF-to-Markdown" --collect-all pymupdf4llm app.py
if errorlevel 1 goto :error

echo.
echo Uygulama hazir: dist\PDF-to-Markdown\PDF-to-Markdown.exe
pause
exit /b 0

:error
echo Paketleme basarisiz oldu.
pause
exit /b 1
