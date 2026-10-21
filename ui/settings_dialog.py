"""
StreamBatch - Settings Dialog
Manages user preferences, download limits, default formats, and FFmpeg configuration.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QFileDialog, QGroupBox, QMessageBox
)
import config
from db.database import Database
from core.ffmpeg_checker import verify_ffmpeg, get_ffmpeg_path

class SettingsDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Settings - StreamBatch")
        self.resize(560, 480)
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # 1. Download Defaults
        gen_group = QGroupBox("General & Queue Preferences")
        gen_layout = QVBoxLayout(gen_group)

        # Default Folder
        f_layout = QHBoxLayout()
        f_layout.addWidget(QLabel("Default Destination:"))
        self.folder_input = QLineEdit()
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_folder)
        f_layout.addWidget(self.folder_input)
        f_layout.addWidget(self.browse_btn)
        gen_layout.addLayout(f_layout)

        # Concurrency
        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel("Max Concurrent Downloads:"))
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 10)
        c_layout.addWidget(self.concurrency_spin)
        c_layout.addStretch()
        gen_layout.addLayout(c_layout)

        # Default format & quality
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Default Format:"))
        self.fmt_combo = QComboBox()
        for f in config.ALL_FORMATS:
            self.fmt_combo.addItem(f["label"], f["id"])
        fmt_layout.addWidget(self.fmt_combo)

        fmt_layout.addWidget(QLabel("Default Quality:"))
        self.quality_combo = QComboBox()
        for q in config.AUDIO_QUALITIES:
            self.quality_combo.addItem(q["label"], q["id"])
        fmt_layout.addWidget(self.quality_combo)
        gen_layout.addLayout(fmt_layout)

        layout.addWidget(gen_group)

        # 2. FFmpeg Configuration
        ffmpeg_group = QGroupBox("FFmpeg Engine Integration")
        ffmpeg_layout = QVBoxLayout(ffmpeg_group)

        ff_desc = QLabel("FFmpeg powers high-quality audio extraction and format conversion.")
        ff_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        ffmpeg_layout.addWidget(ff_desc)

        ff_path_row = QHBoxLayout()
        ff_path_row.addWidget(QLabel("FFmpeg Path:"))
        self.ffmpeg_input = QLineEdit()
        self.ffmpeg_input.setPlaceholderText("Auto-detected or custom C:\\path\\to\\ffmpeg.exe")
        self.ffmpeg_browse = QPushButton("Browse...")
        self.ffmpeg_browse.clicked.connect(self._browse_ffmpeg)
        self.ffmpeg_autodetect = QPushButton("Auto-Detect")
        self.ffmpeg_autodetect.clicked.connect(self._autodetect_ffmpeg)
        ff_path_row.addWidget(self.ffmpeg_input)
        ff_path_row.addWidget(self.ffmpeg_browse)
        ff_path_row.addWidget(self.ffmpeg_autodetect)
        ffmpeg_layout.addLayout(ff_path_row)

        self.ffmpeg_status_lbl = QLabel("")
        self.ffmpeg_status_lbl.setWordWrap(True)
        ffmpeg_layout.addWidget(self.ffmpeg_status_lbl)

        test_row = QHBoxLayout()
        self.verify_btn = QPushButton("Verify FFmpeg Installation")
        self.verify_btn.clicked.connect(self._verify_ffmpeg_status)
        test_row.addWidget(self.verify_btn)
        test_row.addStretch()
        ffmpeg_layout.addLayout(test_row)

        layout.addWidget(ffmpeg_group)

        # 3. Automation & Recovery
        rec_group = QGroupBox("Error Recovery")
        rec_layout = QVBoxLayout(rec_group)
        self.auto_retry_cb = QCheckBox("Automatically retry temporary network dropouts")
        self.notify_cb = QCheckBox("Play notification chime when downloads finish")
        rec_layout.addWidget(self.auto_retry_cb)
        rec_layout.addWidget(self.notify_cb)
        layout.addWidget(rec_group)

        # Buttons
        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._save_settings)

        btn_row.addStretch()
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _load_settings(self):
        def_dir = self.db.get_setting("download_dir", config.DEFAULT_SETTINGS["download_dir"])
        self.folder_input.setText(def_dir)

        concurrency = int(self.db.get_setting("max_concurrent", config.DEFAULT_SETTINGS["max_concurrent"]))
        self.concurrency_spin.setValue(concurrency)

        fmt = self.db.get_setting("default_format", config.DEFAULT_SETTINGS["default_format"])
        idx = self.fmt_combo.findData(fmt)
        if idx >= 0:
            self.fmt_combo.setCurrentIndex(idx)

        q = self.db.get_setting("default_quality", config.DEFAULT_SETTINGS["default_quality"])
        q_idx = self.quality_combo.findData(q)
        if q_idx >= 0:
            self.quality_combo.setCurrentIndex(q_idx)

        ff_custom = self.db.get_setting("custom_ffmpeg_path", "")
        self.ffmpeg_input.setText(ff_custom)

        self.auto_retry_cb.setChecked(self.db.get_setting("auto_retry", "True") == "True")
        self.notify_cb.setChecked(self.db.get_setting("notify_on_complete", "True") == "True")

        self._verify_ffmpeg_status()

    def _browse_folder(self):
        curr = self.folder_input.text().strip()
        chosen = QFileDialog.getExistingDirectory(self, "Select Download Directory", curr)
        if chosen:
            self.folder_input.setText(chosen)

    def _browse_ffmpeg(self):
        curr = self.ffmpeg_input.text().strip()
        chosen, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg Executable", curr, "FFmpeg Executable (ffmpeg.exe);;All Files (*.*)")
        if chosen:
            self.ffmpeg_input.setText(chosen)
            self._verify_ffmpeg_status()

    def _autodetect_ffmpeg(self):
        detected = get_ffmpeg_path()
        if detected:
            self.ffmpeg_input.setText(detected)
            self._verify_ffmpeg_status()
        else:
            QMessageBox.information(self, "Auto-Detect", "No system FFmpeg found in standard locations.")

    def _verify_ffmpeg_status(self):
        path = self.ffmpeg_input.text().strip() or None
        res = verify_ffmpeg(path)
        if res["found"]:
            self.ffmpeg_status_lbl.setText(f"✓ Detected: {res['version']}\nPath: {res['path']}")
            self.ffmpeg_status_lbl.setStyleSheet("color: #34d399; font-size: 11px;")
        else:
            self.ffmpeg_status_lbl.setText(f"✗ FFmpeg Not Found: {res['error']}")
            self.ffmpeg_status_lbl.setStyleSheet("color: #f87171; font-size: 11px;")

    def _save_settings(self):
        self.db.set_setting("download_dir", self.folder_input.text().strip())
        self.db.set_setting("max_concurrent", self.concurrency_spin.value())
        self.db.set_setting("default_format", self.fmt_combo.currentData())
        self.db.set_setting("default_quality", self.quality_combo.currentData())
        self.db.set_setting("custom_ffmpeg_path", self.ffmpeg_input.text().strip())
        self.db.set_setting("auto_retry", str(self.auto_retry_cb.isChecked()))
        self.db.set_setting("notify_on_complete", str(self.notify_cb.isChecked()))
        self.accept()
