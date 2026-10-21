@echo off
setlocal
echo Registering StreamBatch Native Messaging Host for Chrome and Edge...

set "MANIFEST_PATH=%~dp0streambatch_host.json"

:: Chrome Registry Key
REG ADD "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.streambatch.native_host" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f
if %ERRORLEVEL% equ 0 (
    echo [OK] Registered for Google Chrome.
) else (
    echo [FAILED] Chrome registration failed.
)

:: Edge Registry Key
REG ADD "HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.streambatch.native_host" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f
if %ERRORLEVEL% equ 0 (
    echo [OK] Registered for Microsoft Edge.
) else (
    echo [FAILED] Edge registration failed.
)

echo.
echo Native Messaging Host registration completed.
pause
