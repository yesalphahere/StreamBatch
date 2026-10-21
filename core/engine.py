"""
StreamBatch - Core Download Engine & Inspector
Powered by yt-dlp and FFmpeg. Provides inspection, progress hooks, and cancellable worker execution.
"""
import os
import sys
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from PySide6.QtCore import QObject, Signal, QRunnable, Slot

import yt_dlp
from core.formats import build_ydl_opts
from core.ffmpeg_checker import get_ffmpeg_path

logger = logging.getLogger("StreamBatch.Engine")

class DownloadCancelledException(Exception):
    """Raised when a download is cancelled or paused by user."""
    pass

class MediaInspector:
    """
    Inspects URLs (single media or playlists) to extract metadata,
    duration, thumbnails, and playlist entries without downloading media streams.
    """
    @staticmethod
    def inspect(url: str, custom_ffmpeg_path: Optional[str] = None) -> Dict[str, Any]:
        ffmpeg_loc = get_ffmpeg_path(custom_ffmpeg_path)
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",  # fast shallow playlist inspection
            "skip_download": True,
            "no_color": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            }
        }
        if ffmpeg_loc:
            ydl_opts["ffmpeg_location"] = ffmpeg_loc

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise ValueError("Failed to retrieve media information.")

                is_playlist = info.get("_type") == "playlist" or "entries" in info

                if is_playlist:
                    entries = []
                    raw_entries = list(info.get("entries") or [])
                    for idx, e in enumerate(raw_entries, start=1):
                        if not e:
                            continue
                        e_url = e.get("url") or e.get("webpage_url") or ""
                        # If relative or id only
                        if e_url and not e_url.startswith("http"):
                            e_url = f"https://www.youtube.com/watch?v={e_url}"
                        entries.append({
                            "index": idx,
                            "id": e.get("id", f"item_{idx}"),
                            "title": e.get("title", f"Track {idx}"),
                            "duration": int(e.get("duration") or 0),
                            "url": e_url,
                            "uploader": e.get("uploader", "Unknown"),
                            "thumbnail": e.get("thumbnail") or e.get("thumbnails", [{}])[0].get("url", "") if e.get("thumbnails") else ""
                        })

                    return {
                        "is_playlist": True,
                        "title": info.get("title", "Untitled Playlist"),
                        "uploader": info.get("uploader", "Unknown"),
                        "count": len(entries),
                        "entries": entries,
                        "webpage_url": info.get("webpage_url", url),
                    }
                else:
                    return {
                        "is_playlist": False,
                        "id": info.get("id", ""),
                        "title": info.get("title", "Untitled Media"),
                        "duration": int(info.get("duration") or 0),
                        "thumbnail": info.get("thumbnail", ""),
                        "uploader": info.get("uploader", "Unknown"),
                        "webpage_url": info.get("webpage_url", url),
                        "entries": [{
                            "index": 1,
                            "id": info.get("id", ""),
                            "title": info.get("title", "Untitled Media"),
                            "duration": int(info.get("duration") or 0),
                            "url": info.get("webpage_url", url),
                            "uploader": info.get("uploader", "Unknown"),
                            "thumbnail": info.get("thumbnail", "")
                        }]
                    }
        except Exception as e:
            err_msg = str(e)
            # Clean up common yt-dlp error prefixes
            if "ERROR:" in err_msg:
                err_msg = err_msg.split("ERROR:", 1)[1].strip()
            raise RuntimeError(err_msg)


class DownloadWorkerSignals(QObject):
    """Signals emitted by DownloadWorker during operation."""
    started = Signal(str)                                         # item_id
    progress = Signal(str, float, float, int, int, int)           # item_id, percent, speed, eta, downloaded, total
    status_changed = Signal(str, str)                             # item_id, status_str
    completed = Signal(str, str, int)                             # item_id, file_path, file_size
    failed = Signal(str, str)                                     # item_id, error_message
    paused = Signal(str)                                          # item_id
    cancelled = Signal(str)                                       # item_id


class DownloadWorker(QRunnable):
    """
    QRunnable worker executing a single media download/conversion job.
    Supports cancellation, pause, and real-time progress reporting.
    """
    def __init__(
        self,
        item_id: str,
        url: str,
        format_id: str,
        quality_id: str,
        output_dir: str,
        custom_ffmpeg_path: Optional[str] = None
    ):
        super().__init__()
        self.item_id = item_id
        self.url = url
        self.format_id = format_id
        self.quality_id = quality_id
        self.output_dir = output_dir
        self.custom_ffmpeg_path = custom_ffmpeg_path

        self.signals = DownloadWorkerSignals()
        self._is_cancelled = False
        self._is_paused = False
        self._final_filepath = None
        self._last_progress_time = 0.0

    def cancel(self):
        """Instruct worker to abort immediately and discard."""
        self._is_cancelled = True

    def pause(self):
        """Instruct worker to pause (stops gracefully, preserving partial download)."""
        self._is_paused = True

    def _progress_hook(self, d: Dict[str, Any]):
        if self._is_cancelled or self._is_paused:
            raise DownloadCancelledException("Download interrupted by user.")

        status = d.get("status")
        now = time.time()

        if status == "downloading":
            # Throttle UI updates to max 10 per second to keep GUI silky smooth
            if now - self._last_progress_time < 0.1:
                return
            self._last_progress_time = now

            downloaded = d.get("downloaded_bytes") or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            speed = d.get("speed") or 0.0
            eta = d.get("eta") or 0

            percent = 0.0
            if total > 0:
                percent = round((downloaded / total) * 100.0, 2)
            elif downloaded > 0:
                percent = -1.0 # indeterminate or streaming

            self.signals.progress.emit(self.item_id, percent, float(speed), int(eta), int(downloaded), int(total))
            self.signals.status_changed.emit(self.item_id, "DOWNLOADING")

        elif status == "finished":
            # Media stream download finished; moving to post-processing
            self._final_filepath = d.get("filename")
            self.signals.status_changed.emit(self.item_id, "CONVERTING")

    def _postprocessor_hook(self, d: Dict[str, Any]):
        if self._is_cancelled or self._is_paused:
            raise DownloadCancelledException("Download interrupted by user.")

        status = d.get("status")
        if status == "started":
            self.signals.status_changed.emit(self.item_id, "CONVERTING")
        elif status == "finished":
            info_dict = d.get("info_dict", {})
            filepath = info_dict.get("filepath") or d.get("filepath")
            if filepath:
                self._final_filepath = filepath

    @Slot()
    def run(self):
        if self._is_cancelled:
            self.signals.cancelled.emit(self.item_id)
            return
        if self._is_paused:
            self.signals.paused.emit(self.item_id)
            return

        self.signals.started.emit(self.item_id)
        self.signals.status_changed.emit(self.item_id, "DOWNLOADING")

        ydl_opts = build_ydl_opts(
            format_id=self.format_id,
            quality_id=self.quality_id,
            output_dir=self.output_dir,
            progress_hook=self._progress_hook,
            postprocessor_hook=self._postprocessor_hook,
            custom_ffmpeg_path=self.custom_ffmpeg_path
        )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                
                # Determine final file location
                final_file = self._final_filepath
                if not final_file and info:
                    if "_filename" in info:
                        final_file = info["_filename"]
                    elif "requested_downloads" in info and info["requested_downloads"]:
                        final_file = info["requested_downloads"][0].get("filepath")

                # If postprocessing converted the extension (e.g. mp3)
                if final_file:
                    target_ext = self.format_id if self.format_id in ["mp3", "m4a", "flac", "wav", "aac", "opus"] else None
                    if target_ext:
                        base, _ = os.path.splitext(final_file)
                        cand = f"{base}.{target_ext}"
                        if os.path.exists(cand):
                            final_file = cand

                file_size = 0
                if final_file and os.path.exists(final_file):
                    file_size = os.path.getsize(final_file)

                self.signals.completed.emit(self.item_id, final_file or "", file_size)

        except DownloadCancelledException:
            if self._is_cancelled:
                self.signals.cancelled.emit(self.item_id)
            elif self._is_paused:
                self.signals.paused.emit(self.item_id)
        except Exception as e:
            if self._is_cancelled:
                self.signals.cancelled.emit(self.item_id)
            elif self._is_paused:
                self.signals.paused.emit(self.item_id)
            else:
                err_str = str(e)
                if "ERROR:" in err_str:
                    err_str = err_str.split("ERROR:", 1)[1].strip()
                self.signals.failed.emit(self.item_id, err_str)
