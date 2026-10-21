# StreamBatch - Execution Workflow & Media Pipeline

This document describes the step-by-step lifecycle of a media or playlist download within StreamBatch, from URL submission to final audio file generation.

---

## 1. End-to-End Workflow Diagram

```
+----------------+      +-------------------+      +------------------+
| 1. URL Input   | ---> | 2. Inspection     | ---> | 3. Job Creation  |
| - Clipboard    |      | - Fast flat query |      | - Duplicate check|
| - Browser Ext  |      | - Track list parse|      | - Format/Bitrate |
| - Manual Entry |      | - Selective pick  |      | - Persist QUEUED |
+----------------+      +-------------------+      +------------------+
                                                             |
                                                             v
+----------------+      +-------------------+      +------------------+
| 6. Final File  | <--- | 5. Transcoding    | <--- | 4. Download      |
| - Output path  |      | - FFmpeg convert  |      | - QThreadPool    |
| - COMPLETED st |      | - Metadata embed  |      | - Byte resume    |
| - Explorer nav |      | - Transcode tags  |      | - 10 Hz progress |
+----------------+      +-------------------+      +------------------+
```

---

## 2. Detailed Execution Stages

### Stage 1: URL Ingestion & Scheme Validation
1. The user provides a URL through one of three pathways:
   - **Desktop GUI**: Pasted manually or auto-detected from the Windows clipboard.
   - **Browser Extension Popup**: The user clicks the extension icon on an active media tab and selects **Download with StreamBatch**.
   - **Browser Context Menu**: The user right-clicks any video, audio, or link element and chooses **Download with StreamBatch**.
2. **Security Gate**: The URL is validated to verify that it begins with `http://` or `https://`. Non-web schemes (such as `file://`, `ftp://`, `javascript:`, or SMB paths) are rejected immediately.

### Stage 2: Media Inspection & Track Picking
1. The `MediaInspector` invokes `yt-dlp` in non-downloading inspection mode (`extract_flat: "in_playlist"`).
2. If the URL is a **single track**, its title, duration, and channel are extracted.
3. If the URL is a **playlist**, the inspector extracts all child item metadata (index, track title, duration, and target link) within 1–2 seconds.
4. The user is presented with a checklist table:
   - Specific items can be toggled via checkboxes.
   - Preset buttons (**Select All** / **Deselect All**) facilitate rapid batch tuning.
   - The user selects target format (e.g. MP3, M4A, FLAC, WAV) and audio bitrate (e.g. 320 kbps, 256 kbps, 192 kbps).

### Stage 3: Duplicate Verification & Database Insertion
1. StreamBatch queries SQLite (`SELECT id, status, completed_at FROM downloads WHERE url = ?`).
2. If a match is found:
   - The UI surfaces a warning banner indicating that the item was already processed, displaying the timestamp and prior status.
3. Once confirmed, each selected track is assigned a unique UUID and inserted into the `downloads` table with status `QUEUED`.

### Stage 4: Concurrency Scheduling & Stream Retrieval
1. `QueueManager._schedule_next()` counts the active threads running on `QThreadPool`.
2. If active threads < `max_concurrent` (configurable 1–10, default: 3):
   - The next pending job is assigned a `DownloadWorker` instance.
   - The job's status transitions to `DOWNLOADING`.
3. `yt-dlp` handles chunked transport:
   - Emits real-time progress events (`downloaded_bytes`, `total_bytes`, `speed`, `eta`).
   - Signals are throttled to a maximum frequency of 10 Hz (100 ms intervals) before updating the GUI.
   - Partial downloads write to `.part` temporary files on disk.

### Stage 5: Audio Transcoding & Metadata Remuxing
1. Once all transport chunks are received, the worker transitions to `CONVERTING`.
2. StreamBatch invokes the detected `FFmpeg` binary with the appropriate audio extraction arguments:
   - Lossless audio: Transcoded to FLAC or raw WAV PCM.
   - Compressed audio: Transcoded using `libmp3lame` (MP3) or AAC with the configured bitrate (`-b:a 320k`).
   - Tagging: `FFmpegMetadata` writes track titles, artists, and album information into the output file's ID3/container tags.

### Stage 6: Completion & Record Archiving
1. The final transcoded media file is saved to the designated download folder (default: `Downloads\StreamBatch\`).
2. The database updates the job record:
   - Status updated to `COMPLETED`.
   - `output_path` and exact final file size recorded.
   - `completed_at` timestamp committed.
3. The table item delegate changes the row's badge from `DOWNLOADING` to `COMPLETED` (green).
4. The user can right-click the row anytime to execute **Open Media File** or **Open Destination Folder** in Windows Explorer.
