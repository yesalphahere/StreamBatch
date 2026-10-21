"""
StreamBatch - Main Application Window
Coordinates top toolbar actions, download queue table, persistent history, and status updates.
"""
import os
import subprocess
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QMenu, QMessageBox, QAbstractItemView, QApplication
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QAction, QIcon, QFont

import config
from db.database import Database
from core.queue_manager import QueueManager
from core.ffmpeg_checker import verify_ffmpeg
from ui.widgets.progress_delegate import (
    ProgressBarDelegate, StatusBadgeDelegate,
    format_bytes, format_speed, format_eta
)
from ui.add_dialog import AddDownloadDialog
from ui.settings_dialog import SettingsDialog
from ui.history_view import HistoryView

class MainWindow(QMainWindow):
    def __init__(self, db: Database, queue_mgr: QueueManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.queue_mgr = queue_mgr

        self.setWindowTitle(f"{config.APP_NAME} - Media & Batch Download Manager")
        self.resize(1020, 640)
        self.setMinimumSize(850, 500)

        # Map item_id to table row index for lightning fast row updates
        self._row_map: Dict[str, int] = {}

        # Debounce timer: collapse rapid queue_updated signals into one rebuild
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(150)  # ms — coalesce bursts into one redraw
        self._refresh_timer.timeout.connect(self._do_refresh_queue_table)

        self._init_ui()
        self._connect_signals()
        self._do_refresh_queue_table()  # immediate on startup
        self._check_ffmpeg_status()

    def _init_ui(self):
        # 1. Main Toolbar
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.add_act = QAction("+ Add URL / Playlist", self)
        self.add_act.triggered.connect(self.open_add_dialog)
        toolbar.addAction(self.add_act)

        toolbar.addSeparator()

        self.start_all_act = QAction("Start All", self)
        self.start_all_act.triggered.connect(self.queue_mgr.start_all)
        toolbar.addAction(self.start_all_act)

        self.pause_all_act = QAction("Pause All", self)
        self.pause_all_act.triggered.connect(self.queue_mgr.pause_all)
        toolbar.addAction(self.pause_all_act)

        toolbar.addSeparator()

        self.settings_act = QAction("Settings", self)
        self.settings_act.triggered.connect(self.open_settings_dialog)
        toolbar.addAction(self.settings_act)

        # 2. Central Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: Queue View
        queue_widget = QWidget()
        q_layout = QVBoxLayout(queue_widget)
        q_layout.setContentsMargins(10, 10, 10, 10)

        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(6)
        self.queue_table.setHorizontalHeaderLabels([
            "Title / Source", "Format", "Progress", "Speed", "ETA", "Status"
        ])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.queue_table.setColumnWidth(2, 220)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue_table.customContextMenuRequested.connect(self._show_queue_context_menu)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setAlternatingRowColors(True)

        self.progress_delegate = ProgressBarDelegate(self.queue_table)
        self.queue_table.setItemDelegateForColumn(2, self.progress_delegate)

        self.status_delegate = StatusBadgeDelegate(self.queue_table)
        self.queue_table.setItemDelegateForColumn(5, self.status_delegate)

        q_layout.addWidget(self.queue_table)
        self.tabs.addTab(queue_widget, "Active Queue")

        # Tab 2: History View
        self.history_view = HistoryView(self.db)
        self.history_view.redownload_requested.connect(self._on_redownload_requested)
        self.tabs.addTab(self.history_view, "Download History")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # 3. Status Bar
        self.status_bar = self.statusBar()
        self.stats_lbl = QLabel("Active: 0 | Queued: 0")
        self.speed_lbl = QLabel("Speed: --")
        self.ffmpeg_lbl = QLabel("FFmpeg: Checking...")
        self.api_lbl = QLabel("Extension Listener: Active (Port 9654)")

        self.status_bar.addPermanentWidget(self.stats_lbl, 1)
        self.status_bar.addPermanentWidget(self.speed_lbl, 1)
        self.status_bar.addPermanentWidget(self.api_lbl, 1)
        self.status_bar.addPermanentWidget(self.ffmpeg_lbl, 1)

    def _connect_signals(self):
        # queue_updated = structural change (rows added/deleted) → debounced full rebuild
        self.queue_mgr.queue_updated.connect(self._refresh_queue_table)
        # item_progress = frequent tick → lightweight in-place update only
        self.queue_mgr.item_progress.connect(self._on_item_progress)
        # item_status_changed = badge/color update only → lightweight in-place update
        self.queue_mgr.item_status_changed.connect(self._on_item_status_changed)
        self.queue_mgr.stats_updated.connect(self._on_stats_updated)

    def _check_ffmpeg_status(self):
        custom_ffmpeg = self.db.get_setting("custom_ffmpeg_path", "")
        res = verify_ffmpeg(custom_ffmpeg or None)
        if res["found"]:
            self.ffmpeg_lbl.setText("FFmpeg: Ready")
            self.ffmpeg_lbl.setStyleSheet("color: #34d399; font-weight: 500;")
        else:
            self.ffmpeg_lbl.setText("FFmpeg: Not Found")
            self.ffmpeg_lbl.setStyleSheet("color: #f87171; font-weight: 500;")

    def open_add_dialog(self, initial_url: str = ""):
        dlg = AddDownloadDialog(self.db, self, initial_url=initial_url)
        if dlg.exec():
            jobs = getattr(dlg, "generated_jobs", [])
            start_now = getattr(dlg, "start_immediately", False)
            if jobs:
                if len(jobs) == 1:
                    self.queue_mgr.add_job(jobs[0])
                else:
                    self.queue_mgr.add_batch(jobs)

                if start_now:
                    self.queue_mgr.start_all()

    def open_settings_dialog(self):
        dlg = SettingsDialog(self.db, self)
        if dlg.exec():
            # Update concurrency
            concurrency = int(self.db.get_setting("max_concurrent", config.DEFAULT_SETTINGS["max_concurrent"]))
            self.queue_mgr.set_max_concurrent(concurrency)
            self._check_ffmpeg_status()

    def _on_tab_changed(self, index: int):
        if index == 1:
            self.history_view.reload_history()

    def _refresh_queue_table(self):
        """
        Called on structural queue changes (jobs added/deleted).
        Debounced: rapid back-to-back signals collapse into one redraw after 150 ms.
        """
        if not self._refresh_timer.isActive():
            self._refresh_timer.start()

    def _do_refresh_queue_table(self):
        """Actual full-table rebuild — runs at most once per 150 ms."""
        self.queue_table.setUpdatesEnabled(False)
        try:
            items = self.queue_mgr.db.get_all_downloads()
            self.queue_table.setRowCount(len(items))
            self._row_map.clear()

            for row, item in enumerate(items):
                item_id = item["id"]
                self._row_map[item_id] = row

                # Title
                t_str = item.get("title") or item.get("url")
                if item.get("is_playlist") and item.get("playlist_title"):
                    t_str = f"[{item.get('playlist_index', 0)}] {t_str}"
                t_item = QTableWidgetItem(t_str)
                t_item.setData(Qt.UserRole, item_id)
                t_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.queue_table.setItem(row, 0, t_item)

                # Format
                fmt_str = item.get("format", "").upper()
                if item.get("quality"):
                    fmt_str += f" ({item.get('quality')}k)"
                f_item = QTableWidgetItem(fmt_str)
                f_item.setTextAlignment(Qt.AlignCenter)
                f_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.queue_table.setItem(row, 1, f_item)

                # Progress Bar delegate data
                p_item = QTableWidgetItem()
                p_item.setData(Qt.UserRole, {
                    "percent": item.get("progress", 0.0),
                    "downloaded": item.get("downloaded_bytes", 0),
                    "total": item.get("file_size", 0),
                    "status": item.get("status", "QUEUED")
                })
                p_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.queue_table.setItem(row, 2, p_item)

                # Speed
                sp_str = format_speed(item.get("speed", 0.0)) if item.get("status") == "DOWNLOADING" else "--"
                sp_item = QTableWidgetItem(sp_str)
                sp_item.setTextAlignment(Qt.AlignCenter)
                sp_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.queue_table.setItem(row, 3, sp_item)

                # ETA
                eta_str = format_eta(item.get("eta", 0)) if item.get("status") == "DOWNLOADING" else "--"
                eta_item = QTableWidgetItem(eta_str)
                eta_item.setTextAlignment(Qt.AlignCenter)
                eta_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.queue_table.setItem(row, 4, eta_item)

                # Status Badge
                st_item = QTableWidgetItem(item.get("status", "QUEUED"))
                st_item.setTextAlignment(Qt.AlignCenter)
                st_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.queue_table.setItem(row, 5, st_item)
        finally:
            self.queue_table.setUpdatesEnabled(True)

        if self.tabs.currentIndex() == 1:
            self.history_view.reload_history()

    @Slot(str, float, float, int, int, int)
    def _on_item_progress(self, item_id: str, percent: float, speed: float, eta: int, dl: int, total: int):
        row = self._row_map.get(item_id)
        if row is None or row >= self.queue_table.rowCount():
            return

        # Update progress column
        p_item = self.queue_table.item(row, 2)
        if p_item:
            p_item.setData(Qt.UserRole, {
                "percent": percent,
                "downloaded": dl,
                "total": total,
                "status": "DOWNLOADING"
            })
            self.queue_table.update(self.queue_table.visualItemRect(p_item))

        # Update speed
        sp_item = self.queue_table.item(row, 3)
        if sp_item:
            sp_item.setText(format_speed(speed))

        # Update ETA
        eta_item = self.queue_table.item(row, 4)
        if eta_item:
            eta_item.setText(format_eta(eta))

    @Slot(str, str)
    def _on_item_status_changed(self, item_id: str, status: str):
        row = self._row_map.get(item_id)
        if row is None or row >= self.queue_table.rowCount():
            return

        st_item = self.queue_table.item(row, 5)
        if st_item:
            st_item.setText(status)
            self.queue_table.update(self.queue_table.visualItemRect(st_item))

        # Also refresh progress bar data status
        p_item = self.queue_table.item(row, 2)
        if p_item:
            d = p_item.data(Qt.UserRole) or {}
            d["status"] = status
            p_item.setData(Qt.UserRole, d)
            self.queue_table.update(self.queue_table.visualItemRect(p_item))

    @Slot(int, int, int)
    def _on_stats_updated(self, active: int, queued: int, total: int):
        self.stats_lbl.setText(f"Active: {active} | Queued: {queued}")
        if active == 0:
            self.speed_lbl.setText("Speed: --")

    def _show_queue_context_menu(self, pos):
        item = self.queue_table.itemAt(pos)
        if not item:
            return

        row = item.row()
        t_item = self.queue_table.item(row, 0)
        item_id = t_item.data(Qt.UserRole)
        dl_item = self.db.get_download(item_id)
        if not dl_item:
            return

        status = dl_item.get("status", "QUEUED")
        out_path = dl_item.get("output_path", "")
        file_exists = out_path and os.path.exists(out_path)

        menu = QMenu(self)

        # Context actions based on state
        if status in ("DOWNLOADING", "QUEUED"):
            pause_act = QAction("Pause Download", self)
            pause_act.triggered.connect(lambda: self.queue_mgr.pause_job(item_id))
            menu.addAction(pause_act)

            cancel_act = QAction("Cancel Download", self)
            cancel_act.triggered.connect(lambda: self.queue_mgr.cancel_job(item_id))
            menu.addAction(cancel_act)

        elif status in ("PAUSED", "CANCELLED", "ERROR"):
            resume_act = QAction("Resume / Retry", self)
            resume_act.triggered.connect(lambda: self.queue_mgr.resume_job(item_id))
            menu.addAction(resume_act)

        if status == "COMPLETED" or file_exists:
            open_act = QAction("Open Media File", self)
            open_act.triggered.connect(lambda: os.startfile(os.path.normpath(out_path)))
            menu.addAction(open_act)

        if out_path:
            folder_act = QAction("Open Destination Folder", self)
            folder_act.triggered.connect(lambda: self._open_folder(out_path))
            menu.addAction(folder_act)

        menu.addSeparator()

        copy_act = QAction("Copy URL", self)
        copy_act.triggered.connect(lambda: QApplication.clipboard().setText(dl_item.get("url", "")))
        menu.addAction(copy_act)

        del_act = QAction("Remove Job from Queue", self)
        del_act.triggered.connect(lambda: self.queue_mgr.delete_job(item_id))
        menu.addAction(del_act)

        if status == "ERROR":
            err_msg = dl_item.get("error_message") or "Unknown error"
            err_act = QAction(f"Error Details: {err_msg[:40]}...", self)
            err_act.triggered.connect(lambda: QMessageBox.critical(self, "Download Error", f"Job failed with error:\n\n{err_msg}"))
            menu.addAction(err_act)

        menu.exec(self.queue_table.viewport().mapToGlobal(pos))

    def _open_folder(self, path: str):
        folder = os.path.dirname(path) if os.path.isfile(path) else path
        if os.path.exists(folder):
            subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"' if os.path.exists(path) else f'explorer "{folder}"')

    def _on_redownload_requested(self, url: str, fmt: str, quality: str):
        self.tabs.setCurrentIndex(0)
        self.open_add_dialog(initial_url=url)

    def handle_external_url(self, url: str, fmt: str, quality: str):
        """Called by LocalAPIServer when browser extension sends a download URL."""
        self.show()
        self.raise_()
        self.activateWindow()
        self.open_add_dialog(initial_url=url)
