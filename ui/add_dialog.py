"""
StreamBatch - Add Download / Playlist Inspection Dialog
Handles single media analysis, playlist batch inspection, duplicate checks, format/quality configuration.
"""
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QGroupBox, QMessageBox, QProgressBar, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QObject, Slot
from PySide6.QtGui import QClipboard, QGuiApplication

import config
from db.database import Database
from core.engine import MediaInspector
from ui.widgets.progress_delegate import format_duration

class InspectorWorkerSignals(QObject):
    finished = Signal(dict)
    failed = Signal(str)

class InspectorWorker(threading.Thread):
    def __init__(self, url: str, custom_ffmpeg: Optional[str] = None):
        super().__init__(daemon=True)
        self.url = url
        self.custom_ffmpeg = custom_ffmpeg
        self.signals = InspectorWorkerSignals()

    def run(self):
        try:
            res = MediaInspector.inspect(self.url, self.custom_ffmpeg)
            self.signals.finished.emit(res)
        except Exception as e:
            self.signals.failed.emit(str(e))


class AddDownloadDialog(QDialog):
    """
    Dialog allowing users to inspect a URL, preview metadata or playlist tracks,
    choose format & audio quality, detect duplicates, and queue downloads.
    """
    def __init__(self, db: Database, parent=None, initial_url: str = ""):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add Download - StreamBatch")
        self.resize(720, 600)
        self.setMinimumSize(600, 500)

        self._inspected_data = None

        self._init_ui()

        # Check clipboard if no initial URL given
        if initial_url:
            self.url_input.setText(initial_url)
            self._start_inspection()
        else:
            self._check_clipboard()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # 1. URL Input Section
        url_group = QGroupBox("Media or Playlist URL")
        url_layout = QVBoxLayout(url_group)

        input_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube, SoundCloud, or media link here...")
        self.url_input.textChanged.connect(self._on_url_changed)

        self.paste_btn = QPushButton("Paste")
        self.paste_btn.clicked.connect(self._paste_from_clipboard)

        self.inspect_btn = QPushButton("Analyze URL")
        self.inspect_btn.setObjectName("primaryBtn")
        self.inspect_btn.clicked.connect(self._start_inspection)

        input_row.addWidget(self.url_input)
        input_row.addWidget(self.paste_btn)
        input_row.addWidget(self.inspect_btn)
        url_layout.addLayout(input_row)

        # Duplicate Warning Banner
        self.dup_banner = QLabel()
        self.dup_banner.setObjectName("warningBadge")
        self.dup_banner.setWordWrap(True)
        self.dup_banner.hide()
        url_layout.addWidget(self.dup_banner)

        # Progress / Status during inspection
        self.inspect_progress = QProgressBar()
        self.inspect_progress.setRange(0, 0) # Indeterminate spinner
        self.inspect_progress.setFixedHeight(4)
        self.inspect_progress.hide()
        url_layout.addWidget(self.inspect_progress)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        url_layout.addWidget(self.status_lbl)

        layout.addWidget(url_group)

        # 2. Inspected Content Details / Playlist Track Table
        self.content_group = QGroupBox("Detected Media / Playlist Items")
        content_layout = QVBoxLayout(self.content_group)

        self.media_summary_lbl = QLabel("Enter a URL and click 'Analyze URL' to inspect media.")
        self.media_summary_lbl.setStyleSheet("color: #cbd5e1; font-weight: 500;")
        content_layout.addWidget(self.media_summary_lbl)

        # Playlist Batch Controls
        self.batch_bar = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all_tracks)
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all_tracks)
        self.selected_count_lbl = QLabel("")
        self.selected_count_lbl.setStyleSheet("color: #00a8ff; font-weight: 600;")

        self.batch_bar.addWidget(self.select_all_btn)
        self.batch_bar.addWidget(self.deselect_all_btn)
        self.batch_bar.addStretch()
        self.batch_bar.addWidget(self.selected_count_lbl)
        content_layout.addLayout(self.batch_bar)

        # Playlist Items Table
        self.track_table = QTableWidget()
        self.track_table.setColumnCount(4)
        self.track_table.setHorizontalHeaderLabels(["", "#", "Title", "Duration"])
        self.track_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.track_table.setColumnWidth(0, 36)
        self.track_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.track_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.track_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.track_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.track_table.verticalHeader().setVisible(False)
        self.track_table.setAlternatingRowColors(True)
        content_layout.addWidget(self.track_table)

        self.batch_bar_widget = self.batch_bar
        self._toggle_playlist_view(False)

        layout.addWidget(self.content_group)

        # 3. Output Options (Format, Quality, Folder)
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout(options_group)

        row1 = QHBoxLayout()
        # Format
        row1.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        for f in config.ALL_FORMATS:
            self.format_combo.addItem(f["label"], f["id"])
        
        default_fmt = self.db.get_setting("default_format", config.DEFAULT_SETTINGS["default_format"])
        idx = self.format_combo.findData(default_fmt)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        row1.addWidget(self.format_combo)

        # Quality
        self.quality_lbl = QLabel("Quality:")
        row1.addWidget(self.quality_lbl)
        self.quality_combo = QComboBox()
        for q in config.AUDIO_QUALITIES:
            self.quality_combo.addItem(q["label"], q["id"])
        default_q = self.db.get_setting("default_quality", config.DEFAULT_SETTINGS["default_quality"])
        q_idx = self.quality_combo.findData(default_q)
        if q_idx >= 0:
            self.quality_combo.setCurrentIndex(q_idx)
        row1.addWidget(self.quality_combo)

        options_layout.addLayout(row1)

        # Destination Folder
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Save to:"))
        self.folder_input = QLineEdit()
        def_dir = self.db.get_setting("download_dir", config.DEFAULT_SETTINGS["download_dir"])
        self.folder_input.setText(def_dir)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_folder)
        row2.addWidget(self.folder_input)
        row2.addWidget(self.browse_btn)
        options_layout.addLayout(row2)

        layout.addWidget(options_group)

        # 4. Action Buttons
        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.queue_btn = QPushButton("Add to Queue")
        self.queue_btn.clicked.connect(lambda: self._confirm_download(start_immediately=False))

        self.start_btn = QPushButton("Download Now")
        self.start_btn.setObjectName("primaryBtn")
        self.start_btn.clicked.connect(lambda: self._confirm_download(start_immediately=True))

        btn_row.addStretch()
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.queue_btn)
        btn_row.addWidget(self.start_btn)
        layout.addLayout(btn_row)

    def _check_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text().strip()
        if text.startswith("http://") or text.startswith("https://"):
            self.url_input.setText(text)
            self._start_inspection()

    def _paste_from_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self.url_input.setText(text)
            self._start_inspection()

    def _on_url_changed(self, text: str):
        url = text.strip()
        if not url:
            self.dup_banner.hide()
            return
        # Duplicate detection check
        dup = self.db.check_duplicate(url)
        if dup:
            date_str = dup.get("completed_at") or dup.get("created_at") or "earlier"
            status = dup.get("status", "QUEUED")
            title = dup.get("title", "Media item")
            self.dup_banner.setText(
                f"Duplicate Detected: '{title}' is already in your library ({status}, {date_str}). "
                "Adding this will create a new job."
            )
            self.dup_banner.show()
        else:
            self.dup_banner.hide()

    def _on_format_changed(self):
        fmt = self.format_combo.currentData()
        # Hide quality preset for video formats where audio bitrates don't apply directly
        is_video = fmt.startswith("video_")
        self.quality_lbl.setVisible(not is_video)
        self.quality_combo.setVisible(not is_video)

    def _browse_folder(self):
        curr = self.folder_input.text().strip()
        chosen = QFileDialog.getExistingDirectory(self, "Select Download Directory", curr)
        if chosen:
            self.folder_input.setText(chosen)

    def _toggle_playlist_view(self, show_table: bool):
        self.select_all_btn.setVisible(show_table)
        self.deselect_all_btn.setVisible(show_table)
        self.selected_count_lbl.setVisible(show_table)
        self.track_table.setVisible(show_table)

    def _start_inspection(self):
        url = self.url_input.text().strip()
        if not url:
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid web URL starting with http:// or https://")
            return

        self.inspect_btn.setEnabled(False)
        self.inspect_progress.show()
        self.status_lbl.setText("Analyzing media metadata & streams...")
        self.media_summary_lbl.setText("Inspecting link, please wait...")

        custom_ffmpeg = self.db.get_setting("custom_ffmpeg_path", "")
        self.worker = InspectorWorker(url, custom_ffmpeg)
        self.worker.signals.finished.connect(self._on_inspection_finished)
        self.worker.signals.failed.connect(self._on_inspection_failed)
        self.worker.start()

    @Slot(dict)
    def _on_inspection_finished(self, data: dict):
        self.inspect_btn.setEnabled(True)
        self.inspect_progress.hide()
        self.status_lbl.setText("Analysis complete.")
        self._inspected_data = data

        is_playlist = data.get("is_playlist", False)
        title = data.get("title", "Untitled")
        uploader = data.get("uploader", "Unknown")

        if is_playlist:
            entries = data.get("entries", [])
            self.media_summary_lbl.setText(f"Playlist: {title} ({len(entries)} items) - Uploader: {uploader}")
            self._populate_playlist_table(entries)
            self._toggle_playlist_view(True)
        else:
            duration = format_duration(data.get("duration", 0))
            self.media_summary_lbl.setText(f"Title: {title}\nDuration: {duration} | Channel: {uploader}")
            self._toggle_playlist_view(False)

    @Slot(str)
    def _on_inspection_failed(self, error: str):
        self.inspect_btn.setEnabled(True)
        self.inspect_progress.hide()
        self.status_lbl.setText("Inspection failed.")
        self.media_summary_lbl.setText(f"Error inspecting media: {error}")
        QMessageBox.warning(self, "Inspection Failed", f"Could not analyze URL:\n\n{error}")

    def _populate_playlist_table(self, entries: List[dict]):
        self.track_table.blockSignals(True)
        self.track_table.setUpdatesEnabled(False)
        self.track_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            # Native checkable item (lightning fast, scales to 10,000+ items)
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            chk_item.setCheckState(Qt.Checked)
            chk_item.setTextAlignment(Qt.AlignCenter)
            self.track_table.setItem(row, 0, chk_item)

            # Index
            idx_item = QTableWidgetItem(str(entry.get("index", row + 1)))
            idx_item.setTextAlignment(Qt.AlignCenter)
            idx_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.track_table.setItem(row, 1, idx_item)

            # Title
            title_item = QTableWidgetItem(entry.get("title", "Unknown Track"))
            title_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.track_table.setItem(row, 2, title_item)

            # Duration
            dur_str = format_duration(entry.get("duration", 0))
            dur_item = QTableWidgetItem(dur_str)
            dur_item.setTextAlignment(Qt.AlignCenter)
            dur_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.track_table.setItem(row, 3, dur_item)

        self.track_table.setUpdatesEnabled(True)
        self.track_table.blockSignals(False)
        self._update_selected_count()
        if not hasattr(self, "_item_changed_connected"):
            self.track_table.itemChanged.connect(self._on_table_item_changed)
            self._item_changed_connected = True

    def _on_table_item_changed(self, item):
        if item.column() == 0:
            self._update_selected_count()

    def _select_all_tracks(self):
        self.track_table.blockSignals(True)
        self.track_table.setUpdatesEnabled(False)
        for row in range(self.track_table.rowCount()):
            it = self.track_table.item(row, 0)
            if it:
                it.setCheckState(Qt.Checked)
        self.track_table.setUpdatesEnabled(True)
        self.track_table.blockSignals(False)
        self._update_selected_count()

    def _deselect_all_tracks(self):
        self.track_table.blockSignals(True)
        self.track_table.setUpdatesEnabled(False)
        for row in range(self.track_table.rowCount()):
            it = self.track_table.item(row, 0)
            if it:
                it.setCheckState(Qt.Unchecked)
        self.track_table.setUpdatesEnabled(True)
        self.track_table.blockSignals(False)
        self._update_selected_count()

    def _update_selected_count(self):
        total = self.track_table.rowCount()
        sel = 0
        for row in range(total):
            it = self.track_table.item(row, 0)
            if it and it.checkState() == Qt.Checked:
                sel += 1
        self.selected_count_lbl.setText(f"Selected: {sel} / {total}")

    def _confirm_download(self, start_immediately: bool):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter a valid media or playlist URL.")
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL starting with http:// or https://")
            return

        folder = self.folder_input.text().strip()
        if not folder or not Path(folder).exists():
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Invalid Folder", f"Failed to create download directory:\n{e}")
                return

        fmt = self.format_combo.currentData()
        quality = self.quality_combo.currentData()

        # Build items to queue
        jobs = []

        if self._inspected_data and self._inspected_data.get("is_playlist"):
            playlist_title = self._inspected_data.get("title", "Playlist")
            entries = self._inspected_data.get("entries", [])
            for row, entry in enumerate(entries):
                chk = self.track_table.item(row, 0)
                if chk and chk.checkState() == Qt.Checked:
                    jobs.append({
                        "id": str(uuid.uuid4()),
                        "url": entry["url"],
                        "media_id": entry.get("id", ""),
                        "title": entry.get("title", "Track"),
                        "duration": entry.get("duration", 0),
                        "thumbnail": entry.get("thumbnail", ""),
                        "format": fmt,
                        "quality": quality,
                        "output_path": "",
                        "status": "QUEUED",
                        "is_playlist": 1,
                        "playlist_title": playlist_title,
                        "playlist_index": entry.get("index", row + 1)
                    })
        elif self._inspected_data:
            entry = self._inspected_data.get("entries", [{}])[0]
            jobs.append({
                "id": str(uuid.uuid4()),
                "url": url,
                "media_id": self._inspected_data.get("id", ""),
                "title": self._inspected_data.get("title", "Media Item"),
                "duration": self._inspected_data.get("duration", 0),
                "thumbnail": self._inspected_data.get("thumbnail", ""),
                "format": fmt,
                "quality": quality,
                "output_path": "",
                "status": "QUEUED",
                "is_playlist": 0,
                "playlist_title": "",
                "playlist_index": 0
            })
        else:
            # User didn't click analyze, queue raw URL directly
            jobs.append({
                "id": str(uuid.uuid4()),
                "url": url,
                "media_id": "",
                "title": url,
                "duration": 0,
                "thumbnail": "",
                "format": fmt,
                "quality": quality,
                "output_path": "",
                "status": "QUEUED",
                "is_playlist": 0,
                "playlist_title": "",
                "playlist_index": 0
            })

        if not jobs:
            QMessageBox.information(self, "No Items", "No tracks were selected for download.")
            return

        self.generated_jobs = jobs
        self.start_immediately = start_immediately
        self.accept()
