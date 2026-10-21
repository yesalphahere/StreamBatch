"""
StreamBatch - Queue Manager
Orchestrates concurrent download jobs, pauses, resumes, retries, and persistence with SQLite.
"""
import os
import threading
from typing import Dict, Any, List, Optional
from PySide6.QtCore import QObject, Signal, QThreadPool

from db.database import Database
from core.engine import DownloadWorker
import config

class QueueManager(QObject):
    """
    Central queue manager coordinating download concurrency, thread allocation,
    worker lifecycle, and database synchronization.
    """
    # Emitted only when rows are added or removed (triggers full table rebuild)
    queue_updated = Signal()
    # Emitted every progress tick (lightweight — only updates existing rows in-place)
    item_progress = Signal(str, float, float, int, int, int) # id, percent, speed, eta, dl, total
    # Emitted when a single row's status badge changes (lightweight in-place update)
    item_status_changed = Signal(str, str)                   # id, status
    item_completed = Signal(str, str, int)                   # id, filepath, filesize
    item_failed = Signal(str, str)                           # id, error
    stats_updated = Signal(int, int, int)                    # active, queued, total

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.pool = QThreadPool()
        
        self._active_workers: Dict[str, DownloadWorker] = {}
        self._pending_ids: List[str] = []
        self._lock = threading.Lock()

        # Load max concurrent from settings
        max_c = int(self.db.get_setting("max_concurrent", config.DEFAULT_SETTINGS["max_concurrent"]))
        self.set_max_concurrent(max_c)

        # Startup recovery: reset any stale downloading jobs from previous crashes/session
        self.db.reset_interrupted_to_paused()

    def set_max_concurrent(self, value: int):
        val = max(1, min(10, int(value)))
        self.pool.setMaxThreadCount(val)
        self.db.set_setting("max_concurrent", val)
        self._schedule_next()

    def get_max_concurrent(self) -> int:
        return self.pool.maxThreadCount()

    def add_job(self, item_dict: Dict[str, Any]) -> str:
        """Saves item to DB and enqueues it."""
        item_id = self.db.add_download(item_dict)
        with self._lock:
            if item_id not in self._pending_ids and item_id not in self._active_workers:
                self._pending_ids.append(item_id)
        self.queue_updated.emit()
        self._schedule_next()
        return item_id

    def add_batch(self, items: List[Dict[str, Any]]) -> List[str]:
        if not items:
            return []
        ids = self.db.add_batch_downloads(items)
        with self._lock:
            for i_id in ids:
                if i_id not in self._pending_ids and i_id not in self._active_workers:
                    self._pending_ids.append(i_id)
        self.queue_updated.emit()
        self._schedule_next()
        return ids

    def start_all(self):
        """Starts all queued or paused downloads."""
        all_items = self.db.get_all_downloads()
        ids_to_queue = [
            it["id"] for it in all_items
            if it["status"] in ("QUEUED", "PAUSED", "ERROR")
        ]
        if ids_to_queue:
            # Bulk-update statuses in a single DB transaction (not 288 separate writes)
            self.db.bulk_update_status(ids_to_queue, "QUEUED")
        with self._lock:
            for item_id in ids_to_queue:
                if item_id not in self._pending_ids and item_id not in self._active_workers:
                    self._pending_ids.append(item_id)
        self.queue_updated.emit()
        self._schedule_next()

    def pause_all(self):
        """Pauses all currently running downloads and clears the pending queue."""
        with self._lock:
            pending_to_pause = list(self._pending_ids)
            self._pending_ids.clear()
            workers = list(self._active_workers.values())
        # Mark all pending-only jobs as PAUSED in DB (single transaction)
        if pending_to_pause:
            self.db.bulk_update_status(pending_to_pause, "PAUSED")
        # Signal active workers to pause (they will emit paused signal when done)
        for w in workers:
            w.pause()
        self.queue_updated.emit()

    def pause_job(self, item_id: str):
        with self._lock:
            if item_id in self._pending_ids:
                self._pending_ids.remove(item_id)
            worker = self._active_workers.get(item_id)

        self.db.update_status(item_id, "PAUSED")
        self.item_status_changed.emit(item_id, "PAUSED")
        self.queue_updated.emit()

        if worker:
            worker.pause()

    def resume_job(self, item_id: str):
        item = self.db.get_download(item_id)
        if not item:
            return
        self.db.update_status(item_id, "QUEUED")
        self.item_status_changed.emit(item_id, "QUEUED")
        with self._lock:
            if item_id not in self._pending_ids and item_id not in self._active_workers:
                self._pending_ids.append(item_id)
        self.queue_updated.emit()
        self._schedule_next()

    def retry_job(self, item_id: str):
        self.resume_job(item_id)

    def cancel_job(self, item_id: str):
        with self._lock:
            if item_id in self._pending_ids:
                self._pending_ids.remove(item_id)
            worker = self._active_workers.get(item_id)
            
        self.db.update_status(item_id, "CANCELLED")
        self.item_status_changed.emit(item_id, "CANCELLED")
        self.queue_updated.emit()
        self._schedule_next()

        if worker:
            worker.cancel()

    def delete_job(self, item_id: str, delete_file: bool = False):
        self.cancel_job(item_id)
        item = self.db.get_download(item_id)
        if delete_file and item and item.get("output_path"):
            path = item["output_path"]
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        self.db.delete_download(item_id)
        self.queue_updated.emit()

    def _schedule_next(self):
        """Dispatches jobs up to max concurrency slots."""
        with self._lock:
            available_slots = self.pool.maxThreadCount() - len(self._active_workers)
            while available_slots > 0 and self._pending_ids:
                item_id = self._pending_ids.pop(0)
                item = self.db.get_download(item_id)
                if not item or item["status"] not in ("QUEUED", "PAUSED"):
                    continue

                output_dir = self.db.get_setting("download_dir", config.DEFAULT_SETTINGS["download_dir"])
                custom_ffmpeg = self.db.get_setting("custom_ffmpeg_path", "")

                worker = DownloadWorker(
                    item_id=item_id,
                    url=item["url"],
                    format_id=item["format"],
                    quality_id=item["quality"],
                    output_dir=output_dir,
                    custom_ffmpeg_path=custom_ffmpeg
                )

                # Connect worker signals
                worker.signals.started.connect(self._on_worker_started)
                worker.signals.progress.connect(self._on_worker_progress)
                worker.signals.status_changed.connect(self._on_worker_status_changed)
                worker.signals.completed.connect(self._on_worker_completed)
                worker.signals.failed.connect(self._on_worker_failed)
                worker.signals.paused.connect(self._on_worker_paused)
                worker.signals.cancelled.connect(self._on_worker_cancelled)

                self._active_workers[item_id] = worker
                self.pool.start(worker)
                available_slots -= 1

            self._emit_stats()

    def _on_worker_started(self, item_id: str):
        self.db.update_status(item_id, "DOWNLOADING")
        self.item_status_changed.emit(item_id, "DOWNLOADING")
        # No queue_updated here — row already exists, just badge changes

    def _on_worker_progress(self, item_id: str, percent: float, speed: float, eta: int, dl: int, total: int):
        self.db.update_progress(item_id, dl, total, percent, speed, eta)
        self.item_progress.emit(item_id, percent, speed, eta, dl, total)
        # Never emit queue_updated on progress — would cause full 288-row rebuild every tick

    def _on_worker_status_changed(self, item_id: str, status: str):
        self.db.update_status(item_id, status)
        self.item_status_changed.emit(item_id, status)

    def _on_worker_completed(self, item_id: str, file_path: str, file_size: int):
        with self._lock:
            self._active_workers.pop(item_id, None)
        self.db.mark_completed(item_id, file_path, file_size)
        self.item_status_changed.emit(item_id, "COMPLETED")
        self.item_completed.emit(item_id, file_path, file_size)
        self._emit_stats()
        self._schedule_next()
        # queue_updated not needed — row stays, just status changes

    def _on_worker_failed(self, item_id: str, error_message: str):
        with self._lock:
            self._active_workers.pop(item_id, None)
        self.db.update_status(item_id, "ERROR", error_message)
        self.item_status_changed.emit(item_id, "ERROR")
        self.item_failed.emit(item_id, error_message)
        self._emit_stats()
        self._schedule_next()

    def _on_worker_paused(self, item_id: str):
        with self._lock:
            self._active_workers.pop(item_id, None)
        self.db.update_status(item_id, "PAUSED")
        self.item_status_changed.emit(item_id, "PAUSED")
        self._emit_stats()
        self._schedule_next()

    def _on_worker_cancelled(self, item_id: str):
        with self._lock:
            self._active_workers.pop(item_id, None)
        self.db.update_status(item_id, "CANCELLED")
        self.item_status_changed.emit(item_id, "CANCELLED")
        self._emit_stats()
        self._schedule_next()

    def _emit_stats(self):
        active = len(self._active_workers)
        queued = len(self._pending_ids)
        total = active + queued
        self.stats_updated.emit(active, queued, total)
