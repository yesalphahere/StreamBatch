# StreamBatch - Privacy Policy & Data Handling

This document provides a transparent, verifiable overview of how StreamBatch handles user data, local storage, and network communication.

---

## 1. Summary of Data Practices

| Category | Policy / Behavior |
| :--- | :--- |
| **Telemetry & Analytics** | **None.** No usage data, crash logs, or telemetry are collected or sent. |
| **Third-Party Trackers** | **None.** Zero advertising SDKs, tracking pixels, or third-party monitoring. |
| **User Identification** | **Anonymous.** No account creation, login, or personal profile is required. |
| **Data Storage Location** | **100% Local.** Stored exclusively on the user's hard drive in SQLite WAL format. |
| **Network Requests** | **User-Initiated Only.** Outbound traffic occurs solely to fetch media streams requested by the user. |

---

## 2. Local Data Storage

All persistent application data is stored locally in the user's application data directory:
- **Windows Path**: `%LOCALAPPDATA%\StreamBatch\streambatch.db` (or `~/.streambatch/streambatch.db`).

The SQLite database contains:
1. **`downloads` Table**:
   - URL and media identifier.
   - Title, duration, and thumbnail link (if provided by the media host).
   - Format and quality preferences.
   - Output file path on the local filesystem.
   - Download status (`QUEUED`, `DOWNLOADING`, `COMPLETED`, `PAUSED`, `ERROR`).
   - Timestamps (`created_at`, `completed_at`).
2. **`settings` Table**:
   - Key-value preferences (e.g., max concurrent downloads, default output directory, default bitrate).

**Data Erasure**: The user can clear the download history at any time using the **Clear Completed** button in the History tab, or by deleting the `streambatch.db` file.

---

## 3. Network Communication

StreamBatch initiates network communication under the following conditions:

1. **Media Metadata Analysis**: When the user clicks **Analyze URL**, `yt-dlp` transmits an HTTP request to the designated media host to retrieve title, format, and playlist structure.
2. **Media Stream Download**: When a job starts, `yt-dlp` connects to the media host's content delivery network (CDN) to fetch audio or video chunks.
3. **Local IPC Server**: Operates purely within the machine on `127.0.0.1:9654`. No external incoming connections are permitted or accepted.

StreamBatch does not check for updates or ping home servers.
