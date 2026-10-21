"""
StreamBatch - Format and Conversion Preset Builder
Translates user format and quality choices into optimal yt-dlp configurations.
"""
from typing import Dict, Any, List, Optional
import config
from core.ffmpeg_checker import get_ffmpeg_path

def build_ydl_opts(
    format_id: str,
    quality_id: str,
    output_dir: str,
    filename_template: Optional[str] = None,
    progress_hook = None,
    postprocessor_hook = None,
    custom_ffmpeg_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Builds yt-dlp options dictionary tailored for the requested format and quality.
    """
    ffmpeg_loc = get_ffmpeg_path(custom_ffmpeg_path)
    
    if not filename_template:
        filename_template = "%(title)s [%(id)s].%(ext)s"

    outtmpl = f"{output_dir}/{filename_template}"

    opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 5,
        "fragment_retries": 5,
        "continuedl": True,
        "noprogress": False,
        "updatetime": False,
        "windowsfilenames": True,
        "restrictfilenames": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
    }

    if ffmpeg_loc:
        opts["ffmpeg_location"] = ffmpeg_loc

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]
    if postprocessor_hook:
        opts["postprocessor_hooks"] = [postprocessor_hook]

    # Map format presets
    audio_formats = {"mp3", "m4a", "flac", "wav", "aac", "opus"}

    if format_id in audio_formats:
        opts["format"] = "bestaudio/best"
        postprocessors: List[Dict[str, Any]] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": format_id,
            }
        ]
        if quality_id and quality_id != "0":
            postprocessors[0]["preferredquality"] = str(quality_id)

        # Embed metadata if possible
        postprocessors.append({"key": "FFmpegMetadata"})
        opts["postprocessors"] = postprocessors

    elif format_id == "best_audio":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{"key": "FFmpegMetadata"}]

    elif format_id == "video_1080p":
        opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best"
        opts["merge_output_format"] = "mp4"

    elif format_id == "video_720p":
        opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best"
        opts["merge_output_format"] = "mp4"

    elif format_id == "video_best":
        opts["format"] = "bestvideo+bestaudio/best"
        opts["merge_output_format"] = "mp4"

    else:
        # Default fallback to MP3
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality_id or "320"
            },
            {"key": "FFmpegMetadata"}
        ]

    return opts
