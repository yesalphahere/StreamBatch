# Pre-Release Technical & Security Audit

**Project:** StreamBatch (Desktop Media & Batch Automation Manager)  
**Date of Audit:** October 2026  
**Auditor Persona:** Senior Software Engineer, Repository Maintainer, Technical Writer & Security Reviewer  
**Audience:** Technical Recruiters, Open-Source Contributors, Engineering Evaluators

---

## 1. Executive Summary

StreamBatch is a desktop media retrieval, audio extraction, and queue automation tool written in Python 3, PySide6, and `yt-dlp`, integrated with an FFmpeg conversion pipeline and an optional Manifest V3 browser extension. 

The software was conceived to solve a real-world, personal automation challenge: converting online educational and cultural playlists (such as Sufi kalams and qawwalis) into compatible, offline audio files for a family member's keypad mobile phone.

This audit evaluates the codebase's architecture, security boundaries, licensing constraints, code hygiene, and readiness for a public GitHub portfolio.

---

## 2. Actual Technical Stack & Dependencies

| Component | Technology | Version / Specification | License |
| :--- | :--- | :--- | :--- |
| **Core Runtime** | Python | 3.10+ (Verified on 3.14.3 64-bit) | PSF License |
| **GUI Framework** | PySide6-Essentials | 6.12.0 (Qt 6.12 Widgets, Core, Gui) | LGPLv3 |
| **Media Extraction** | `yt-dlp` | 2026.8.19+ | The Unlicense (Public Domain) |
| **Transcoding & Remux** | FFmpeg | Essentials 9.0.1 (Gyan build) | LGPL 2.1+ / GPL 2+ |
| **Persistence** | SQLite3 | Python Standard Library (WAL mode) | Public Domain |
| **Local IPC Server** | `http.server` | Python Standard Library (Port 9654) | PSF License |
| **Browser Extension** | Chrome Extensions API | Manifest V3 (Service Worker) | Open Architecture |
| **Packaging Tool** | PyInstaller | Optional build target | GPLv2+ / Apache 2.0 |

---

## 3. Verified Features vs. Gaps & Planned Enhancements

### A. Implemented & Verified Features
- **Modern Dark Desktop GUI**: Custom QSS stylesheet (`DARK_THEME_QSS`) with responsive tables, custom QStyledItemDelegates for multi-state progress bars and status badges.
- **Media & Playlist Inspection**: Shallow flat extraction (`extract_flat: "in_playlist"`) retrieving playlist titles, duration, and track indexes in seconds without downloading media payloads.
- **Selective Batch Processing**: Interactive playlist checklist table allowing granular item selection (select all, deselect all, custom pick).
- **Multi-Format Transcoding**: Audio profiles for MP3, M4A, FLAC, WAV, AAC, Opus, and HD Video presets (Best, 1080p, 720p).
- **Audio Bitrate Configuration**: 320 kbps, 256 kbps, 192 kbps, 128 kbps, and Source/VBR 0.
- **Queue Control**: Non-blocking `QThreadPool` queue manager supporting job queuing, pausing, resuming (with `.part` file continuation), cancelling, and retrying.
- **Persistent SQLite History**: Full session persistence in WAL mode with duplicate URL detection and historical lookup.
- **FFmpeg Detection**: Multi-path search detecting `winget`, `AppData`, `PATH`, and custom specified binaries.
- **Manifest V3 Extension**: Browser action popup and right-click context menu communicating via local HTTP loopback (`127.0.0.1:9654`) and Native Messaging manifest.

### B. Partially Implemented / Gaps
- **Extension Origin Verification**: The local HTTP loopback currently sets `Access-Control-Allow-Origin: *`. While functional for browser extensions, any browser tab running malicious JavaScript on localhost could technically ping the port. A shared secret token or strict origin header check is recommended for production hardening.
- **Subprocess Error Feedback**: While errors during extraction are surfaced to the database and UI, advanced FFmpeg-level transcoding errors (e.g. corrupt input stream) are grouped under generic runtime exceptions.

### C. Planned / Roadmap Features
- Global bandwidth throttling slider.
- Automated download scheduling (overnight window).
- Subtitle (`.srt`/`.vtt`) extraction and container embedding.
- High-resolution album cover art embedding in audio metadata.

---

## 4. Security & Privacy Audit

### A. Attack Surface & Input Validation
1. **URL Injection & Scheme Validation**: 
   - *Risk*: Passing unvalidated URLs to CLI or engine wrappers could risk protocol smuggling (e.g., `file://`, `smb://`, or malicious arguments).
   - *Remediation*: Enforce strict URL scheme whitelisting (`http://` and `https://`) at both the API server and UI layers.
2. **Local HTTP Server Exposure (Port 9654)**:
   - *Boundary*: Bound strictly to `127.0.0.1` (IPv4 loopback). Not accessible to remote network hosts.
   - *Cross-Origin Requests (CORS)*: Currently allows `*` for seamless extension access. Hardening advice documented in `docs/SECURITY.md`.
3. **Command & Path Injection**:
   - Subprocess executions (`subprocess.run`, `subprocess.Popen`) use argument lists rather than raw shell strings (`shell=False`), preventing shell metacharacter injection.
   - Filenames are sanitized through `yt-dlp`'s `windowsfilenames: True` pipeline, eliminating invalid NTFS characters (`: * ? " < > |`) and directory traversal escapes (`../`).

### B. Data Collection & Privacy Review
- **Telemetry**: Zero telemetry, zero analytics tracking, zero crash reporting sent to third parties.
- **Data Retention**: Download history, URLs, and settings are stored locally on disk in `~/.streambatch/streambatch.db` (or user's `LOCALAPPDATA`).
- **Network Requests**: Outbound network requests occur exclusively to the endpoints provided by the user for media retrieval.

---

## 5. Third-Party Licensing Review

1. **PySide6 (Qt)**: Licensed under **LGPLv3**. Commercial distribution of compiled PyInstaller binaries requires keeping PySide6 dynamically linked so users can replace the Qt libraries if desired.
2. **yt-dlp**: Licensed under **The Unlicense** (Public Domain). Highly permissive; no attribution strictly mandated, but credited in project documentation.
3. **FFmpeg**: Licensed under **LGPLv2.1+** or **GPLv2+** depending on compilation flags. Distributing pre-compiled FFmpeg binaries alongside the installer triggers copyleft distribution obligations. Therefore, StreamBatch's architecture intentionally uses **dynamic system discovery** (`winget`, system `PATH`, or user path) rather than bundling proprietary/copyleft binaries into the source tree.

---

## 6. Repository Hygiene & Cleanup Candidates

- **`__pycache__/` and `*.pyc`**: Present across `core/`, `db/`, and `ui/`. Must be ignored via `.gitignore` and omitted from tracking.
- **Temporary databases (`*.db`, `*.db-wal`, `*.db-shm`)**: Must never be committed to git.
- **Personal Paths & Machine-Specific Artifacts**: Any local absolute path hardcodings should be verified and replaced with `Path.home()` or relative configurations.
- **Test Artifacts**: `test_streambatch.py` creates unique ephemeral SQLite test databases that are purged upon test completion.

---

## 7. Action Plan for Public Release

1. **Phase 2: Cleanup**:
   - Create comprehensive, production-grade `.gitignore`.
   - Remove compiled bytecode caches.
   - Harden input validation on URL entry points.
2. **Phase 3: Documentation**:
   - Rewrite `README.md` to reflect genuine personal origin story, truthful capabilities, and non-exaggerated claims.
   - Author modular guides in `docs/`: `ARCHITECTURE.md`, `WORKFLOW.md`, `INSTALLATION.md`, `USER_GUIDE.md`, `SECURITY.md`, `PRIVACY.md`, `TESTING.md`, `ROADMAP.md`.
   - Provide explicit licensing guidance.
3. **Phase 5: Visual Assets**:
   - Build SVG architecture and workflow diagrams.
   - Prepare clean visual asset placeholders and prompt blueprints in `docs/GRAPHICS_GENERATION_PROMPTS.md`.
4. **Phase 6: Verification**:
   - Expand `test_streambatch.py` with queue lifecycle and URL validation tests.
   - Confirm all tests pass.
