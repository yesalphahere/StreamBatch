"""
StreamBatch - Persistent Download History View
Searchable download archive with duplicate lookup, folder opener, and redownload triggers.
"""
import os
import subprocess
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from db.database import Database
from ui.widgets.progress_delegate import StatusBadgeDelegate, format_bytes

class HistoryView(QWidget):
    redownload_requested = Signal(str, str, str) # url, format, quality

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()
        self.reload_history()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Top Bar: Search and actions
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history by title, URL or format...")
        self.search_input.textChanged.connect(self.reload_history)
        top_bar.addWidget(self.search_input)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.reload_history)
        top_bar.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("Clear Completed")
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.clicked.connect(self._clear_completed)
        top_bar.addWidget(self.clear_btn)

        layout.addLayout(top_bar)

        # History Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Title", "Format", "Size", "Status", "Date", "Output Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Interactive)
        self.table.setColumnWidth(5, 200)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.status_delegate = StatusBadgeDelegate(self.table)
        self.table.setItemDelegateForColumn(3, self.status_delegate)

        layout.addWidget(self.table)

    def reload_history(self):
        self.table.setUpdatesEnabled(False)
        try:
            query = self.search_input.text().strip()
            items = self.db.get_history_items(query)
            self.table.setRowCount(len(items))

            for row, item in enumerate(items):
                # Title
                t_item = QTableWidgetItem(item.get("title") or "Unknown")
                t_item.setData(Qt.UserRole, item["id"])
                t_item.setData(Qt.UserRole + 1, item)
                t_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(row, 0, t_item)

                # Format
                fmt_str = f"{item.get('format', '').upper()} ({item.get('quality', '')}k)" if item.get('quality') else item.get('format', '').upper()
                f_item = QTableWidgetItem(fmt_str)
                f_item.setTextAlignment(Qt.AlignCenter)
                f_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(row, 1, f_item)

                # Size
                s_val = item.get("file_size") or item.get("downloaded_bytes") or 0
                s_item = QTableWidgetItem(format_bytes(s_val))
                s_item.setTextAlignment(Qt.AlignCenter)
                s_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(row, 2, s_item)

                # Status
                st_item = QTableWidgetItem(item.get("status", "QUEUED"))
                st_item.setTextAlignment(Qt.AlignCenter)
                st_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(row, 3, st_item)

                # Date
                d_val = item.get("completed_at") or item.get("created_at") or ""
                if "T" in d_val:
                    d_val = d_val.replace("T", " ")[:19]
                d_item = QTableWidgetItem(d_val)
                d_item.setTextAlignment(Qt.AlignCenter)
                d_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(row, 4, d_item)

                # Path
                p_val = item.get("output_path") or ""
                p_item = QTableWidgetItem(p_val)
                p_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(row, 5, p_item)
        finally:
            self.table.setUpdatesEnabled(True)

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        item_data = self.table.item(row, 0).data(Qt.UserRole + 1)
        if not item_data:
            return

        menu = QMenu(self)
        open_file_act = QAction("Open File", self)
        open_folder_act = QAction("Open Containing Folder", self)
        redownload_act = QAction("Re-download / Retry", self)
        copy_url_act = QAction("Copy Source URL", self)
        del_act = QAction("Remove from History", self)

        out_path = item_data.get("output_path", "")
        file_exists = out_path and os.path.exists(out_path)
        open_file_act.setEnabled(file_exists)
        open_folder_act.setEnabled(bool(out_path))

        open_file_act.triggered.connect(lambda: self._open_file(out_path))
        open_folder_act.triggered.connect(lambda: self._open_folder(out_path))
        redownload_act.triggered.connect(lambda: self._redownload(item_data))
        copy_url_act.triggered.connect(lambda: self._copy_url(item_data.get("url", "")))
        del_act.triggered.connect(lambda: self._delete_item(item_data["id"]))

        menu.addAction(open_file_act)
        menu.addAction(open_folder_act)
        menu.addSeparator()
        menu.addAction(redownload_act)
        menu.addAction(copy_url_act)
        menu.addSeparator()
        menu.addAction(del_act)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_file(self, path: str):
        if path and os.path.exists(path):
            os.startfile(os.path.normpath(path))

    def _open_folder(self, path: str):
        if path:
            folder = os.path.dirname(path) if os.path.isfile(path) else path
            if os.path.exists(folder):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"' if os.path.exists(path) else f'explorer "{folder}"')

    def _copy_url(self, url: str):
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(url)

    def _redownload(self, item_data: dict):
        self.redownload_requested.emit(
            item_data["url"],
            item_data.get("format", "mp3"),
            item_data.get("quality", "320")
        )

    def _delete_item(self, item_id: str):
        self.db.delete_download(item_id)
        self.reload_history()

    def _clear_completed(self):
        reply = QMessageBox.question(
            self, "Clear Completed",
            "Are you sure you want to remove all completed entries from history? Downloaded files on disk will NOT be deleted.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.clear_completed()
            self.reload_history()
