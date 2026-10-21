# StreamBatch

<p align="center">
  <img src="assets/branding/banner.png" alt="StreamBatch — Desktop Media Automation" width="100%">
</p>

<p align="center">
  A desktop application for playlist management, batch media downloads, and audio conversion.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52" alt="PySide6">
  <img src="https://img.shields.io/badge/Media-yt--dlp%20%7C%20FFmpeg-0078D4" alt="yt-dlp and FFmpeg">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57" alt="SQLite">
</p>

---

## About the Project

StreamBatch started with a simple problem at home. My grandfather uses a basic keypad phone, and I wanted to make it easier for him to listen to audio offline. Preparing files one by one was time-consuming, especially when dealing with larger playlists.

So, I built StreamBatch to make the process easier. It lets users select items from supported playlists, manage downloads through a queue, and convert media into different formats for offline playback.

What started as a small personal project grew into an exploration of **automation, efficient workflows, and reliable software tools**. The goal was simple: reduce repetitive manual work and make everyday tasks easier to manage.

## Features

- **Desktop GUI:** A dark interface built with PySide6 and Qt.
- **Playlist Selection:** Inspect supported playlists and choose individual tracks for processing.
- **Audio Conversion:** Export audio to MP3, M4A, FLAC, WAV, AAC, and Opus using FFmpeg.
- **Quality Options:** Select supported audio bitrate profiles and variable-bitrate settings.
- **Video Downloads:** Download and combine available video and audio streams into MP4 files, with supported quality options.
- **Background Processing:** Use a worker pool to process queued tasks without blocking the interface.
- **Queue Controls:** Pause, resume, cancel, and retry tasks where supported.
- **Persistent History:** Store queue state and download history in SQLite, with duplicate URL detection.
- **FFmpeg Discovery:** Check common installation locations and the system PATH.
- **Browser Integration:** A Chrome/Edge Manifest V3 extension sends supported media links to the desktop application through a local HTTP endpoint.

<p align="center">
  <img src="assets/screenshots/dashboard.svg" alt="StreamBatch application interface" width="95%">
</p>

## How It Works

StreamBatch separates the user interface from background media processing and local data storage.

```text
Browser Extension / User Input
             |
             v
      PySide6 Desktop GUI
             |
             v
     Queue Manager
       /       \
      v         v
 Media Engine   SQLite
 yt-dlp         Queue & History
 FFmpeg
```

- **Interface:** Handles user input, settings, history, and queue controls.
- **Queue Manager:** Coordinates background tasks and task states.
- **Media Engine:** Uses yt-dlp and FFmpeg for media retrieval and conversion.
- **Database:** Stores queue information and history between sessions.
- **Browser Extension:** Passes supported media links to the desktop application.

For the detailed design and processing sequence, see [Architecture](docs/ARCHITECTURE.md) and [Workflow](docs/WORKFLOW.md).

## Audio Quality Note

Converting compressed online audio to FLAC or WAV does not restore audio data lost during the original compression. Similarly, choosing a higher MP3 bitrate does not recover missing information.

StreamBatch focuses on format compatibility and convenient offline playback, rather than artificial audio enhancement.

## Installation

### Requirements

- Python 3.10 or later
- FFmpeg
- Windows
- Project dependencies listed in `requirements.txt`

### Setup

```powershell
# Clone the repository
git clone https://github.com/yesalphahere/StreamBatch.git
cd StreamBatch

# Install dependencies
python -m pip install -r requirements.txt

# Start the application
python app.py
```

For a silent launch on Windows, you can use:

```powershell
pythonw app.py
```

See the [Installation Guide](docs/INSTALLATION.md) for additional setup instructions.

## Testing

Run the automated test suite with:

```powershell
python test_streambatch.py
```

The documented test coverage includes database operations, FFmpeg detection, local IPC communication, queue state transitions, and URL validation.

See [Testing Documentation](docs/TESTING.md) for the test cases and known limitations. Check the actual test output before reporting a passing test count.

## Responsible Use

Use StreamBatch only for media you own, content in the public domain, appropriately licensed material, or content you are otherwise authorized to retrieve.

- Respect the terms of service of the media provider.
- Do not use the application to bypass DRM, paywalls, authentication, or access restrictions.
- Follow applicable copyright laws and licensing conditions.

The application's actual security properties depend on its implementation and configuration. See [Security Documentation](docs/SECURITY.md) for the documented security considerations.

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | Application components and threading design |
| [Workflow](docs/WORKFLOW.md) | From URL input to media output |
| [Installation](docs/INSTALLATION.md) | Setup and Windows launch instructions |
| [User Guide](docs/USER_GUIDE.md) | Track selection, formats, and queue controls |
| [Security](docs/SECURITY.md) | Input validation, threat considerations, and reporting |
| [Privacy](docs/PRIVACY.md) | Data handling, telemetry, and retention |
| [Testing](docs/TESTING.md) | Test cases, commands, and known limitations |
| [Roadmap](docs/ROADMAP.md) | Planned improvements and future features |

## Current Limitations

- Media availability and supported formats depend on the source platform.
- FFmpeg must be installed and discoverable for the relevant conversion features.
- Browser integration requires the desktop application and extension to be configured correctly.
- Platform changes may affect media retrieval.

See the [Roadmap](docs/ROADMAP.md) for planned improvements.

## License

## License

StreamBatch is released under the MIT License, allowing others to use, modify, and distribute the software in accordance with its terms. See the [LICENSE](LICENSE) file for the full license text.
