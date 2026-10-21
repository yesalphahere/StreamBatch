"""
StreamBatch - FFmpeg Detector and Verifier
Locates FFmpeg across Windows system locations, user paths, and provides diagnostics.
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import config

def get_possible_ffmpeg_paths() -> list:
    """Returns list of common locations where FFmpeg might reside on Windows."""
    paths = []
    
    # 1. PATH environment
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        paths.append(Path(which_ffmpeg))
        
    # 2. Local app bin directory
    app_bin = Path(__file__).resolve().parent.parent / "bin" / "ffmpeg.exe"
    if app_bin.exists():
        paths.append(app_bin)
        
    # 3. WinGet installation paths in LocalAppData
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_pkgs = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_pkgs.exists():
            for ffmpeg_exe in winget_pkgs.glob("**/ffmpeg.exe"):
                paths.append(ffmpeg_exe)
                
        # Common manual install path
        common_local = Path(local_app_data) / "ffmpeg" / "bin" / "ffmpeg.exe"
        if common_local.exists():
            paths.append(common_local)

    # 4. Program Files & Chocolatey / Scoop
    for base in [os.environ.get("ProgramFiles", "C:\\Program Files"), os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")]:
        if base:
            p = Path(base) / "ffmpeg" / "bin" / "ffmpeg.exe"
            if p.exists():
                paths.append(p)
                
    scoop_ffmpeg = Path.home() / "scoop" / "apps" / "ffmpeg" / "current" / "bin" / "ffmpeg.exe"
    if scoop_ffmpeg.exists():
        paths.append(scoop_ffmpeg)
        
    choco_ffmpeg = Path("C:/ProgramData/chocolatey/bin/ffmpeg.exe")
    if choco_ffmpeg.exists():
        paths.append(choco_ffmpeg)
        
    return paths

def get_ffmpeg_path(custom_path: Optional[str] = None) -> Optional[str]:
    """Returns valid ffmpeg executable path or None if not found."""
    if custom_path and os.path.isfile(custom_path):
        return custom_path
        
    candidates = get_possible_ffmpeg_paths()
    if candidates:
        return str(candidates[0].resolve())
        
    return None

def verify_ffmpeg(executable_path: Optional[str] = None) -> Dict[str, Any]:
    """Runs `ffmpeg -version` and parses the output."""
    path = executable_path or get_ffmpeg_path()
    if not path:
        return {
            "found": False,
            "path": None,
            "version": None,
            "error": "FFmpeg executable not found on the system."
        }
        
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        proc = subprocess.run(
            [path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo,
            timeout=5
        )
        if proc.returncode == 0:
            first_line = proc.stdout.splitlines()[0] if proc.stdout else "FFmpeg (version detected)"
            return {
                "found": True,
                "path": str(path),
                "version": first_line,
                "error": None
            }
        else:
            return {
                "found": False,
                "path": str(path),
                "version": None,
                "error": f"FFmpeg returned exit code {proc.returncode}"
            }
    except Exception as e:
        return {
            "found": False,
            "path": str(path),
            "version": None,
            "error": str(e)
        }
