# StreamBatch - Test Suite & Quality Assurance Documentation

This document describes the automated test suite, execution procedures, test fixtures, coverage boundaries, and known testing gaps.

---

## 1. Test Suite Architecture (`test_streambatch.py`)

StreamBatch features an automated unit and integration test suite using Python's standard `unittest` framework. All tests run against ephemeral, dynamically generated SQLite databases (`test_streambatch_<uuid>.db`) to ensure zero side-effects on user data.

```
+----------------------------------------------------------------------------------+
|                            AUTOMATED TEST SUITE                                  |
|                                                                                  |
|  [ test_01_ffmpeg_detection ] -----------------> Verifies system FFmpeg binary  |
|  [ test_02_database_operations_and_duplicates ]> Verifies SQLite WAL CRUD & dups |
|  [ test_03_format_builder ] -------------------> Validates audio/video presets   |
|  [ test_04_local_api_server ] -----------------> Health check & /add IPC         |
|  [ test_05_queue_state_transitions ] ----------> QueueManager lifecycle states   |
|  [ test_06_url_validation_and_safety ] --------> Blocks protocol smuggling & XSS|
|  [ test_07_filename_safety_and_path_traversal ]> Verifies safe Windows paths     |
|  [ test_08_duplicate_detection_edge_cases ] ---> Whitespace trimming & URL logic |
+----------------------------------------------------------------------------------+
```

---

## 2. Test Execution

### Running the Full Test Suite
Run the test runner directly from the repository root:
```powershell
python test_streambatch.py
```

### Expected Output
```text
........
----------------------------------------------------------------------
Ran 8 tests in 2.682s

OK

[TEST FFmpeg] Found: True, Path: C:\Users\...\ffmpeg.exe
```

---

## 3. Detailed Test Catalog

| Test Name | Component | Verified Logic |
| :--- | :--- | :--- |
| `test_01_ffmpeg_detection` | `core/ffmpeg_checker.py` | Locates FFmpeg binary on system, executes `-version` query, and parses version output safely. |
| `test_02_database_operations_and_duplicates` | `db/database.py` | Validates insertion, progress percentage persistence, duplicate record detection, and completed state updates. |
| `test_03_format_builder` | `core/formats.py` | Validates `yt-dlp` options builder for MP3 (320k), FLAC (Lossless), and MP4 video containers. |
| `test_04_local_api_server` | `core/api_server.py` | Starts localhost HTTP server on ephemeral port (9655), tests `GET /health` and `POST /add` JSON payloads. |
| `test_05_queue_state_transitions` | `core/queue_manager.py` | Verifies job lifecycle transitions: `QUEUED` &rarr; `DOWNLOADING` &rarr; `PAUSED` &rarr; `RESUMED` &rarr; `CANCELLED` &rarr; `DELETED`. |
| `test_06_url_validation_and_safety` | `core/api_server.py` | Verifies rejection (HTTP 400) of illegal schemes: `file://`, `javascript:`, `smb://`, `ftp://`, and empty strings. |
| `test_07_filename_safety_and_path_traversal` | `core/formats.py` | Verifies `windowsfilenames: True` and enforces safe template structure. |
| `test_08_duplicate_detection_edge_cases` | `db/database.py` | Verifies duplicate detection matches URLs even when untrimmed with leading/trailing whitespace. |

---

## 4. Headless GUI Sanity Verification

To verify that all PySide6 Qt dialogs, table delegates, stylesheets, and signals load properly without launching an interactive window:

```powershell
python -c "import sys; from PySide6.QtWidgets import QApplication; from db.database import Database; from core.queue_manager import QueueManager; from ui.main_window import MainWindow; from ui.add_dialog import AddDownloadDialog; from ui.settings_dialog import SettingsDialog; from ui.history_view import HistoryView; from ui.styles import DARK_THEME_QSS; app = QApplication.instance() or QApplication(sys.argv); app.setStyleSheet(DARK_THEME_QSS); db = Database('test_sanity.db'); qm = QueueManager(db); win = MainWindow(db, qm); add_dlg = AddDownloadDialog(db, win); set_dlg = SettingsDialog(db, win); hist = HistoryView(db); db.close(); import os; [os.remove(f) for f in os.listdir('.') if f.startswith('test_sanity.db')]; print('All GUI components verified successfully!')"
```

---

## 5. Known Testing Gaps & Future Work

1. **Simulated High-Latency Network Conditions**: Automated tests currently run over loopback sockets. A simulated network throttler using mock proxies would enhance long-term resilience testing.
2. **Headless Browser Extension Integration**: The Chrome extension popup and background service worker were manually verified; adding a Puppeteer / Playwright test harness would automate end-to-end browser clicking tests.
