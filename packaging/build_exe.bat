@echo off
setlocal
echo ========================================================
echo   StreamBatch - Windows Executable Packaging Script
echo ========================================================

echo 1. Checking dependencies...
python -m pip install pyinstaller PySide6-Essentials yt-dlp

echo 2. Packaging StreamBatch into standalone Windows build...
cd /d "%~dp0"
pyinstaller --clean --noconfirm streambatch.spec

echo.
if exist "dist\StreamBatch\StreamBatch.exe" (
    echo ========================================================
    echo [SUCCESS] StreamBatch build finished!
    echo Executable path: %~dp0dist\StreamBatch\StreamBatch.exe
    echo ========================================================
) else (
    echo [ERROR] Packaging failed. Please check output log above.
)
pause
