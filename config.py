"""
StreamBatch - Configuration and Global Constants
"""
import os
import sys
from pathlib import Path

APP_NAME = "StreamBatch"
APP_VERSION = "1.0.0"

# Directories
USER_HOME = Path.home()
DEFAULT_DOWNLOAD_DIR = USER_HOME / "Downloads" / "StreamBatch"
APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(USER_HOME / ".streambatch"))) / "StreamBatch"
try:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

try:
    DEFAULT_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

# Database
DB_PATH = APP_DATA_DIR / "streambatch.db"

# Local API / Loopback server for Browser Extension & IPC
LOCAL_SERVER_HOST = "127.0.0.1"
LOCAL_SERVER_PORT = 9654

# Default Settings
DEFAULT_SETTINGS = {
    "download_dir": str(DEFAULT_DOWNLOAD_DIR),
    "max_concurrent": 3,
    "default_format": "mp3",
    "default_quality": "320",
    "custom_ffmpeg_path": "",
    "auto_retry": True,
    "max_retries": 3,
    "notify_on_complete": True,
    "theme": "dark"
}

# Supported Audio Formats
AUDIO_FORMATS = [
    {"id": "mp3", "label": "MP3 Audio (.mp3)", "ext": "mp3", "type": "audio"},
    {"id": "m4a", "label": "M4A Audio (.m4a)", "ext": "m4a", "type": "audio"},
    {"id": "flac", "label": "FLAC Lossless (.flac)", "ext": "flac", "type": "audio"},
    {"id": "wav", "label": "WAV Lossless (.wav)", "ext": "wav", "type": "audio"},
    {"id": "aac", "label": "AAC Audio (.aac)", "ext": "aac", "type": "audio"},
    {"id": "opus", "label": "Opus Audio (.opus)", "ext": "opus", "type": "audio"},
    {"id": "best_audio", "label": "Original Best Audio Source", "ext": "best", "type": "audio"}
]

# Supported Video Formats
VIDEO_FORMATS = [
    {"id": "video_best", "label": "Best Video + Audio (.mp4/.mkv)", "ext": "mp4", "type": "video"},
    {"id": "video_1080p", "label": "1080p Full HD (.mp4)", "ext": "mp4", "type": "video"},
    {"id": "video_720p", "label": "720p HD (.mp4)", "ext": "mp4", "type": "video"},
]

ALL_FORMATS = AUDIO_FORMATS + VIDEO_FORMATS

# Audio Quality Presets (kbps)
AUDIO_QUALITIES = [
    {"id": "320", "label": "320 kbps (Extreme / High Quality)"},
    {"id": "256", "label": "256 kbps (Very High Quality)"},
    {"id": "192", "label": "192 kbps (Standard Quality)"},
    {"id": "128", "label": "128 kbps (Space Saving)"},
    {"id": "0", "label": "Best Available (VBR 0 / Source)"}
]
