"""
StreamBatch - Local IPC / Loopback HTTP Server
Enables browser extensions, CLI tools, and external scripts to send URLs to StreamBatch.
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from PySide6.QtCore import QObject, Signal
import config

class APIServerSignals(QObject):
    url_received = Signal(str, str, str) # url, format, quality

class _RequestHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/health", "/status", "/"):
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {
                "status": "online",
                "app": config.APP_NAME,
                "version": config.APP_VERSION
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/add":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body) if body else {}

                url = data.get("url", "").strip()
                fmt = data.get("format", config.DEFAULT_SETTINGS["default_format"])
                quality = data.get("quality", config.DEFAULT_SETTINGS["default_quality"])

                # Security: Validate URL scheme to prevent protocol smuggling
                if not url or not (url.startswith("http://") or url.startswith("https://")):
                    self.send_response(400)
                    self._set_cors_headers()
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid or missing URL. Must begin with http:// or https://"}).encode("utf-8"))
                    return

                app = getattr(self.server, "app_ref", None)
                if app:
                    if app.signals:
                        app.signals.url_received.emit(url, fmt, quality)
                    if app.callback:
                        app.callback(url, fmt, quality)

                self.send_response(200)
                self._set_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "received", "url": url}).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self._set_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence default stderr logging
        return

class _ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

class LocalAPIServer:
    def __init__(self, host: str = config.LOCAL_SERVER_HOST, port: int = config.LOCAL_SERVER_PORT, callback=None):
        self.host = host
        self.port = port
        self.callback = callback
        self.signals = APIServerSignals()
        self._server = None
        self._thread = None

    def start(self):
        try:
            self._server = _ReusableHTTPServer((self.host, self.port), _RequestHandler)
            self.port = self._server.server_address[1]
            self._server.app_ref = self
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
        except Exception as e:
            # Server port already in use or cannot bind
            pass

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
