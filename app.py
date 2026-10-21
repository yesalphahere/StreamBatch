"""
StreamBatch - Modern Desktop Media & Batch Download Manager
Entry point initializing the PySide6 UI, database, background queue manager, and local extension API.
"""
import sys
import os

# Ensure local modules are resolvable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import config
from db.database import Database
from core.queue_manager import QueueManager
from core.api_server import LocalAPIServer
from ui.main_window import MainWindow
from ui.styles import DARK_THEME_QSS

def main():
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName("StreamBatch")
    app.setStyleSheet(DARK_THEME_QSS)

    # Database
    db = Database()

    # Queue Manager
    queue_mgr = QueueManager(db)

    # Main Dashboard Window
    window = MainWindow(db, queue_mgr)

    # Local API Server for Browser Extension integration
    api_server = LocalAPIServer()
    api_server.signals.url_received.connect(window.handle_external_url)
    api_server.start()

    window.show()

    exit_code = app.exec()

    # Graceful shutdown
    api_server.stop()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
