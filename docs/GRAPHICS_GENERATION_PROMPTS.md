# Graphics Generation Prompts & Visual Asset Specifications

This guide contains production-ready visual asset specifications and text-to-image prompts for regenerating or extending the graphics used in the **StreamBatch** engineering portfolio.

---

## 1. Project Banner Graphic

- **Target File:** `assets/branding/streambatch_banner.png` (or `.svg`)
- **Dimensions:** 1200 x 320 px (Aspect Ratio: 3.75:1)
- **Format:** Lossless PNG (or vector SVG)
- **Palette:**
  - Background: Dark slate gradient (`#0f1117` to `#1a1c24`)
  - Accent / Primary: Electric Blue / Azure (`#0078d4`, `#00a8ff`)
  - Text & Accents: Crisp white (`#ffffff`), Slate gray (`#94a3b8`)
- **Composition:**
  - Left: Clean, stylized app icon (rounded square badge with an audio frequency waveform morphing into a download vector arrow).
  - Center-Left: Bold typography "StreamBatch" with subtext: "Desktop Media Retrieval & Batch Audio Transcoding Engine".
  - Bottom-Left: Subtle modular tags: `Python 3 + PySide6`, `yt-dlp & FFmpeg`, `SQLite WAL DB`, `Manifest V3 Extension`, `Local Processing`.
  - Right: Minimalist abstract dark-mode network topology / data stream visualization with soft blue glow.
- **Negative Constraints:**
  - No fake GitHub stars, download counters, or marketing hype ("#1 tool", "10x faster").
  - No cartoonish mascots, 3D glossy bevels, or cluttered backgrounds.
  - No copyrighted platform logos (e.g. YouTube, Spotify logos).
- **Prompt:**
  ```text
  A sleek, developer-focused wide GitHub repository banner, dimensions 1200x320, dark mode aesthetic. Dark charcoal and slate background (#0f1117 to #161922) with a very subtle technical grid pattern. On the left, an elegant icon featuring a stylized audio frequency waveform converging into a modern downward download chevron with an electric cyan and deep azure gradient (#00a8ff to #0078d4). The bold typography reads 'StreamBatch' in clean modern sans-serif, with smaller subtitle 'Desktop Media Retrieval & Batch Audio Transcoding Engine'. Technical pill tags at the bottom. Clean, high-tech, restrained engineering portfolio aesthetic, studio lighting, hyper-clean vector lines, no noise, no clutter, no brand logos.
  ```

---

## 2. Desktop Application Interface Mockup / Hero Render

- **Target File:** `assets/screenshots/dashboard.png` (or `.svg`)
- **Dimensions:** 1920 x 1080 px (16:9)
- **Format:** Lossless PNG
- **Palette:**
  - Window frame: `#1a1c23`
  - Table backgrounds: Alternating `#181b24` and `#14161d`
  - Accents: Emerald green `#10b981`, Dodger blue `#0078d4`, Purple `#8b5cf6`
- **Composition:**
  - Modern Windows desktop application window running on Windows 11 dark mode.
  - Top action bar with clean buttons: "+ Add URL / Playlist", "Start All", "Pause All", "Settings".
  - Two tabs: "Active Queue" (active) and "Download History".
  - A clean data grid showing three jobs:
    1. A live download showing progress bar at 72%, speed 2.4 MB/s, status pill "DOWNLOADING" in blue.
    2. An audio conversion showing status pill "CONVERTING" in purple with FFmpeg processing indicator.
    3. A queued track showing status pill "QUEUED" in neutral dark gray.
  - Bottom status bar displaying queue counts, global bandwidth, and FFmpeg detection status ("FFmpeg: Ready").
- **Negative Constraints:**
  - No real personal user paths (must use generic paths like `C:\Users\username\Downloads\StreamBatch`).
  - No copyrighted video thumbnails or proprietary music covers.
  - Realistic UI elements matching Qt / PySide6 widgets rather than web browser frames.
- **Prompt:**
  ```text
  Realistic high-resolution UI screenshot of a modern Windows 11 desktop software utility in dark mode named StreamBatch. The window has a clean dark slate theme (#1a1c23) with a minimalist top toolbar featuring buttons '+ Add URL / Playlist', 'Start All', 'Pause All', and 'Settings'. A tab widget shows 'Active Queue' and 'Download History'. The main view is a high-contrast data table with columns: Title, Format, Progress bar, Speed, ETA, and Status. The table rows display queued audio jobs (MP3 320k, FLAC Lossless) with blue and purple progress bars and pill badges labeled 'DOWNLOADING', 'CONVERTING', and 'QUEUED'. Bottom status bar showing 'Active: 1 | Queued: 1 | FFmpeg: Ready'. Crisp typography (Segoe UI), professional desktop application software engineering style.
  ```

---

## 3. Architecture & Data Flow Diagram

- **Target File:** `assets/diagrams/architecture.png` (or `.svg`)
- **Dimensions:** 1200 x 680 px
- **Format:** Vector SVG or high-resolution PNG
- **Composition:**
  - 3 primary tiers arranged left to right:
    1. *Ingestion Layer*: Manifest V3 Browser Extension & Local HTTP Server (`127.0.0.1:9654`).
    2. *Application Core*: PySide6 Qt GUI, Queue Manager, and `QThreadPool` worker slots.
    3. *Engine & Storage*: `yt-dlp` stream extraction, `FFmpeg` transcoding, and `SQLite` WAL database.
  - Clear directional arrows indicating synchronous vs asynchronous boundaries.
- **Negative Constraints:**
  - Avoid overlapping text or unreadable small fonts.
  - High contrast for readability across dark and light GitHub themes.
