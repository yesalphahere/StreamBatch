# StreamBatch - User Guide & Operational Manual

This guide covers daily operations, batch workflows, audio/video configuration, and queue management in StreamBatch.

---

## 1. Main Dashboard Overview

The StreamBatch dashboard is split into three functional zones:

1. **Top Action Bar**: Quick-access triggers for adding URLs, starting the queue, pausing active transfers, and opening Settings.
2. **Central View Area**: Two switchable tabs:
   - **Active Queue**: Displays running, queued, paused, and converting jobs with real-time progress indicators.
   - **Download History**: Searchable archive of all historical downloads with direct folder/file openers.
3. **Bottom Status Bar**: Shows aggregate active worker count, queued items, global network throughput, local API listener status, and FFmpeg engine readiness.

---

## 2. Downloading Media

### A. Downloading a Single Audio or Video Link
1. Copy the target media URL to your clipboard.
2. Click **+ Add URL / Playlist** on the top toolbar (or press `Ctrl+N`).
3. If a valid URL is on your clipboard, StreamBatch auto-populates the input field.
4. Click **Analyze URL**. StreamBatch extracts the title, duration, and channel metadata.
5. Under **Download Options**:
   - Select your target format (e.g. `MP3 Audio (.mp3)` or `Best Video + Audio`).
   - Choose your desired audio quality (e.g. `320 kbps` for maximum clarity).
   - Verify the destination folder.
6. Click **Download Now** to start immediately, or **Add to Queue** to hold it until you start the batch.

### B. Batch Processing a Full Playlist
1. Paste a playlist or album link into the URL field and click **Analyze URL**.
2. StreamBatch queries the playlist hierarchy and displays a track checklist table.
3. Use the **Select All** or **Deselect All** buttons to quickly adjust your selection, or check/uncheck individual tracks.
4. Choose the output format and bitrate (these settings apply uniformly across all selected tracks).
5. Click **Download Now**. Each track is enqueued as an independent job and processed according to your concurrency limits.

---

## 3. Managing the Download Queue

Each row in the **Active Queue** tab provides real-time metrics:
- **Title / Source**: Media title, original URL, and playlist context.
- **Format**: Target output codec and bitrate (e.g., `MP3 (320k)`).
- **Progress**: Visual progress bar with percent complete and downloaded/total bytes.
- **Speed**: Live transfer throughput (e.g., `2.4 MB/s`).
- **ETA**: Remaining download time in `mm:ss` or `hh:mm:ss`.
- **Status**: Color-coded pill (`DOWNLOADING`, `CONVERTING`, `QUEUED`, `PAUSED`, `ERROR`, `COMPLETED`).

### Context Menu Actions
Right-click on any row in the queue to access contextual actions:
- **Pause Download**: Safely pauses the worker while preserving the `.part` chunk.
- **Resume / Retry**: Picks up a paused or failed job from its existing byte offset.
- **Cancel Download**: Aborts the active transfer.
- **Open Media File**: Launches the converted media file in your default audio player.
- **Open Destination Folder**: Opens Windows Explorer with the specific file highlighted.
- **Copy URL**: Copies the source URL to your clipboard.
- **Remove Job from Queue**: Deletes the job record from the active queue.
- **Error Details**: If a job fails (e.g., HTTP 403, network drop), click to inspect the raw engine error.

---

## 4. Configuring Settings

Click **Settings** on the top toolbar to adjust global behaviors:

1. **Default Destination**: The folder where completed media files are organized.
2. **Max Concurrent Downloads**: Sets the thread pool size (1 to 10).
   - *Recommendation*: Use `2` or `3` for standard home broadband; use `5` or higher on high-speed fiber connections.
3. **Default Format & Quality**: Sets the preselected format and bitrate for newly analyzed URLs.
4. **FFmpeg Engine Integration**:
   - Displays the detected FFmpeg binary path and version.
   - Allows setting a custom `ffmpeg.exe` path manually.
   - Click **Verify FFmpeg Installation** to perform a diagnostic check.

---

## 5. Using the Browser Extension

StreamBatch includes a companion extension for Google Chrome, Microsoft Edge, and Brave.

### Direct Download via Context Menu
1. While browsing any website, right-click a video, audio player, or media link.
2. Select **Download with StreamBatch**.
3. The URL is dispatched directly to StreamBatch via the local loopback server (`127.0.0.1:9654`).
4. The desktop application activates, opens the **Add Download** dialog, and pre-populates the URL.

### Quick Ingestion via Popup
1. Click the StreamBatch icon in your browser toolbar.
2. The popup displays the URL of your current tab.
3. Select your desired format and audio quality directly in the popup.
4. Click **Download with StreamBatch**.
