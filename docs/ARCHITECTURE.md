# StreamBatch - Architectural Specification

StreamBatch is engineered around a modular, non-blocking architecture designed to balance fast media stream retrieval, CPU-intensive audio transcoding, and responsive user interaction.

---

## 1. High-Level Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                                INGESTION LAYER                                    |
|                                                                                   |
|  [ Chrome/Edge Extension (MV3) ] ---> [ Local IPC Server: http://127.0.0.1:9654 ] |
|  [ Native Messaging Connector  ] ---> [ Standard I/O Pipe (Optional)           ] |
|  [ Manual Clipboard Monitor    ] ---> [ PySide6 Add Dialog Input Field          ] |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                           PRESENTATION & CORE GUI                                 |
|                                                                                   |
|  [ MainWindow (PySide6) ] <---> [ AddDownloadDialog (Playlist Checklist)        ] |
|  [ HistoryView (Search) ] <---> [ SettingsDialog (Concurrency & FFmpeg Path)    ] |
|  [ Table Delegates      ] <---> [ Custom Progress & Status Badge Renderers      ] |
+------------------------------------------+----------------------------------------+
                                           | Qt Signal/Slot Boundary
                                           v
+-----------------------------------------------------------------------------------+
|                             QUEUE & CONCURRENCY                                   |
|                                                                                   |
|  [ QueueManager ] -------------------> [ QThreadPool (Configurable 1 to 10 slots)] |
|         |                                        |                                |
|         | Dispatches Job                         v                                |
|         +----------------------------> [ DownloadWorker (QRunnable Instance)   ] |
+--------------------------------------------------+--------------------------------+
                                                   |
                        +--------------------------+--------------------------+
                        |                                                     |
                        v                                                     v
+---------------------------------------------+ +-----------------------------------+
|               PROCESSING ENGINE             | |            PERSISTENCE            |
|                                             | |                                   |
| [ yt-dlp ]: Stream Retrieval & Flat Parser  | | [ SQLite (WAL Mode) ]             |
| [ FFmpeg ]: Audio Extract & Transcoding     | |  - downloads (Queue & History)    |
| [ Hooks  ]: 10 Hz Throttled Progress Signals| |  - settings (Key-Value Config)    |
+---------------------------------------------+ +-----------------------------------+
```

---

## 2. Component Breakdown

### A. Presentation Layer (`ui/`)
- **`MainWindow` (`ui/main_window.py`)**: The primary coordinator of the user interface. Hosts the top toolbar actions, active queue table, and history tab. Handles IPC signals emitted by the background HTTP loopback server.
- **`AddDownloadDialog` (`ui/add_dialog.py`)**: Provides URL validation and background inspection via `MediaInspector`. For playlists, it dynamically renders a multi-select checklist table with track durations and indices.
- **`SettingsDialog` (`ui/settings_dialog.py`)**: Exposes runtime concurrency tuning (1 to 10 simultaneous workers), default audio bitrate presets, and FFmpeg executable path overrides.
- **`HistoryView` (`ui/history_view.py`)**: Displays the searchable historical log of downloads with native Windows Explorer file and folder opening integrations.
- **`ProgressBarDelegate` & `StatusBadgeDelegate` (`ui/widgets/progress_delegate.py`)**: Custom `QStyledItemDelegate` subclasses that draw hardware-accelerated progress bars and colored status pills directly into table viewports.

### B. Concurrency & Queue Engine (`core/queue_manager.py`)
- **Worker Model**: Utilizes Qt's `QThreadPool` and `QRunnable` architecture.
- **State Machine**:
  - `QUEUED`: Stored in database, awaiting an available thread slot.
  - `DOWNLOADING`: Stream chunks actively arriving over HTTP/HTTPS.
  - `CONVERTING`: Media download complete; FFmpeg process performing audio extraction and remuxing.
  - `COMPLETED`: Transcoded file written to destination; metadata updated.
  - `PAUSED`: Download halted cleanly; byte-range `.part` files preserved for resumption.
  - `CANCELLED`: Worker aborted and discarded.
  - `ERROR`: Network timeout, authentication roadblock, or format parsing failure captured cleanly.
- **Signal Throttling**: Progress hooks throttle UI update events to a maximum frequency of 10 Hz (every 100 ms). This prevents GUI thread saturation and guarantees consistent 60 FPS responsiveness during multi-megabyte transfers.

### C. Media Retrieval & Processing Pipeline (`core/engine.py` & `core/formats.py`)
- **Shallow Playlist Introspection**: The `MediaInspector.inspect()` method queries URLs using `extract_flat: "in_playlist"`. This returns full playlist hierarchies in hundreds of milliseconds without downloading audio or video streams.
- **Transcoding Matrix (`core/formats.py`)**:
  - Direct conversion to **MP3, M4A, FLAC (Lossless), WAV (Lossless), AAC**, and **Opus**.
  - Merged video presets for **1080p, 720p**, and **Best Video+Audio**.
  - Selectable bitrate profiles (`320k`, `256k`, `192k`, `128k`, `Source/0`).
  - Automatic metadata embedding via `FFmpegMetadata` post-processor.

### D. FFmpeg Auto-Detection (`core/ffmpeg_checker.py`)
- Discovers system FFmpeg binaries across common Windows locations:
  1. Explicit user path configured in SQLite settings.
  2. Windows system `PATH` (via `shutil.which`).
  3. WinGet package repositories (`%LOCALAPPDATA%\Microsoft\WinGet\Packages\...`).
  4. Scoop and Chocolatey installation paths.
  5. Local application `bin/` directory.

### E. Persistence Layer (`db/database.py`)
- **SQLite Engine**: Configured with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and `PRAGMA synchronous=NORMAL`.
- **Concurrency Safety**: Ensures thread-local database connections, allowing background `DownloadWorker` threads to record progress ticks while the main GUI queries historical records without lock collisions.
- **Crash Recovery**: Automatically scans active queue records on startup and switches interrupted `DOWNLOADING` or `CONVERTING` tasks to `PAUSED`, enabling one-click resumption.

### F. Local IPC Server (`core/api_server.py`)
- Standard Python `http.server` running in a daemon thread on `127.0.0.1:9654`.
- Accepts JSON payloads from browser extensions:
  - `GET /health` / `GET /status`: Verifies desktop application availability.
  - `POST /add`: Validates URL schemes (`http://` or `https://`) and passes download requests directly to the main Qt event loop.
