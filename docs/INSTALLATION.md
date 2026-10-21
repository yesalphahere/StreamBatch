# StreamBatch - Installation & Setup Guide (Windows)

This document contains step-by-step setup instructions for running StreamBatch on Microsoft Windows.

---

## 1. Prerequisites

Before installing StreamBatch, verify that your machine has the following dependencies:

1. **Python 3.10 or Higher**
   - Download from [python.org](https://www.python.org/downloads/) or install via Windows Terminal:
     ```powershell
     winget install Python.Python.3.12
     ```
   - Ensure the option **"Add Python to PATH"** is checked during installation.
   - Verify in PowerShell:
     ```powershell
     python --version
     ```

2. **FFmpeg**
   - FFmpeg is required for extracting audio streams and transcoding into formats like MP3, FLAC, and WAV.
   - Install Gyan's FFmpeg Essentials build via WinGet:
     ```powershell
     winget install Gyan.FFmpeg.Essentials --source winget
     ```
   - Restart your PowerShell window and verify:
     ```powershell
     ffmpeg -version
     ```
   > **Note:** StreamBatch features an intelligent multi-path locator that automatically discovers FFmpeg if installed via WinGet, Scoop, Chocolatey, or placed directly in `bin/ffmpeg.exe`.

---

## 2. Setting Up the Application

### Step 1: Clone or Download the Repository
```powershell
git clone https://github.com/yesalphahere/StreamBatch.git
cd StreamBatch
```

### Step 2: Install Python Dependencies
Install the required packages from `requirements.txt`:
```powershell
python -m pip install -r requirements.txt
```

The primary dependencies are:
- `PySide6-Essentials`: Hardware-accelerated Qt6 desktop widgets.
- `yt-dlp`: Supported media extraction engine.

---

## 3. Launching StreamBatch

### Option A: From the Terminal
```powershell
python app.py
```

### Option B: Silent Launch (No Command Window)
Launch using Python's GUI launcher:
```powershell
pythonw app.py
```

### Option C: Create a Desktop Shortcut
Run this one-line command in PowerShell to generate a desktop shortcut:
```powershell
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\StreamBatch.lnk'); $s.TargetPath = 'pythonw.exe'; $s.Arguments = '\"' + (Get-Location).Path + '\app.py\"'; $s.WorkingDirectory = (Get-Location).Path; $s.Save()"
```

---

## 4. Setting Up the Browser Extension (Optional)

StreamBatch includes a Manifest V3 browser extension for Google Chrome, Microsoft Edge, and Brave.

1. Open your browser and navigate to:
   - **Chrome**: `chrome://extensions`
   - **Edge**: `edge://extensions`
2. Enable **Developer mode** (toggle in top-right corner).
3. Click **Load unpacked**.
4. Select the `extension/` directory inside your StreamBatch folder:
   ```
   C:\path\to\StreamBatch\extension
   ```
5. *(Optional for Native Messaging)*: Double-click `extension\native_host\install_host.bat` to register the native messaging host in the Windows Registry.

---

## 5. Building a Standalone Windows Executable (.exe)

If you wish to bundle StreamBatch into a standalone `.exe` distribution:

1. Install PyInstaller:
   ```powershell
   python -m pip install pyinstaller
   ```
2. Run the packaging batch script:
   ```powershell
   .\packaging\build_exe.bat
   ```
3. The compiled binary will be placed in:
   ```
   packaging\dist\StreamBatch\StreamBatch.exe
   ```
