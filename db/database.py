"""
StreamBatch - SQLite Database Layer
Persistent download queue, history tracking, and settings management.
"""
import sqlite3
import threading
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import config

class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[Path] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._db_path = str(db_path or config.DB_PATH)
                cls._instance._local = threading.local()
                cls._instance._init_db()
            return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for high concurrency
            self._local.conn.execute("PRAGMA journal_mode=WAL;")
            self._local.conn.execute("PRAGMA synchronous=NORMAL;")
        return self._local.conn

    def _init_db(self):
        conn = self._get_connection()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    media_id TEXT,
                    title TEXT NOT NULL,
                    duration INTEGER DEFAULT 0,
                    thumbnail TEXT,
                    format TEXT NOT NULL,
                    quality TEXT DEFAULT '320',
                    output_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    downloaded_bytes INTEGER DEFAULT 0,
                    progress REAL DEFAULT 0.0,
                    speed REAL DEFAULT 0.0,
                    eta INTEGER DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'QUEUED',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    is_playlist INTEGER DEFAULT 0,
                    playlist_title TEXT,
                    playlist_index INTEGER DEFAULT 0
                );
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_url ON downloads(url);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status);
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

            # Populate defaults if missing
            for key, val in config.DEFAULT_SETTINGS.items():
                conn.execute("""
                    INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);
                """, (key, str(val)))

    def add_download(self, item: Dict[str, Any]) -> str:
        self.add_batch_downloads([item])
        return item["id"]

    def add_batch_downloads(self, items: List[Dict[str, Any]]) -> List[str]:
        """Bulk-inserts or updates multiple download records in a single atomic transaction."""
        if not items:
            return []
        conn = self._get_connection()
        now_str = datetime.datetime.now().isoformat()
        records = []
        ids = []
        for item in items:
            ids.append(item["id"])
            records.append((
                item["id"],
                item["url"],
                item.get("media_id", ""),
                item.get("title", "Unknown Title"),
                item.get("duration", 0),
                item.get("thumbnail", ""),
                item.get("format", "mp3"),
                item.get("quality", "320"),
                item.get("output_path", ""),
                item.get("file_size", 0),
                item.get("downloaded_bytes", 0),
                item.get("progress", 0.0),
                item.get("speed", 0.0),
                item.get("eta", 0),
                item.get("status", "QUEUED"),
                item.get("error_message", None),
                item.get("created_at", now_str),
                1 if item.get("is_playlist") else 0,
                item.get("playlist_title", ""),
                item.get("playlist_index", 0)
            ))

        with conn:
            conn.executemany("""
                INSERT OR REPLACE INTO downloads (
                    id, url, media_id, title, duration, thumbnail, format, quality,
                    output_path, file_size, downloaded_bytes, progress, speed, eta,
                    status, error_message, created_at, is_playlist, playlist_title, playlist_index
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                );
            """, records)
        return ids

    def update_progress(self, item_id: str, downloaded_bytes: int, total_bytes: int, progress: float, speed: float, eta: int, status: Optional[str] = None):
        conn = self._get_connection()
        with conn:
            if status:
                conn.execute("""
                    UPDATE downloads
                    SET downloaded_bytes = ?, file_size = ?, progress = ?, speed = ?, eta = ?, status = ?
                    WHERE id = ?;
                """, (downloaded_bytes, total_bytes, progress, speed, eta, status, item_id))
            else:
                conn.execute("""
                    UPDATE downloads
                    SET downloaded_bytes = ?, file_size = ?, progress = ?, speed = ?, eta = ?
                    WHERE id = ?;
                """, (downloaded_bytes, total_bytes, progress, speed, eta, item_id))

    def update_status(self, item_id: str, status: str, error_message: Optional[str] = None):
        conn = self._get_connection()
        with conn:
            conn.execute("""
                UPDATE downloads
                SET status = ?, error_message = ?
                WHERE id = ?;
            """, (status, error_message, item_id))

    def bulk_update_status(self, item_ids: List[str], status: str):
        """Updates status for many items in a single atomic transaction."""
        if not item_ids:
            return
        conn = self._get_connection()
        with conn:
            conn.executemany(
                "UPDATE downloads SET status = ? WHERE id = ?;",
                [(status, iid) for iid in item_ids]
            )

    def mark_completed(self, item_id: str, final_path: str, file_size: int = 0):
        conn = self._get_connection()
        now_str = datetime.datetime.now().isoformat()
        with conn:
            conn.execute("""
                UPDATE downloads
                SET status = 'COMPLETED',
                    output_path = ?,
                    file_size = CASE WHEN ? > 0 THEN ? ELSE file_size END,
                    progress = 100.0,
                    speed = 0.0,
                    eta = 0,
                    completed_at = ?,
                    error_message = NULL
                WHERE id = ?;
            """, (final_path, file_size, file_size, now_str, item_id))

    def check_duplicate(self, url: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, url, title, format, status, output_path, created_at, completed_at
            FROM downloads
            WHERE url = ?
            ORDER BY created_at DESC LIMIT 1;
        """, (url.strip(),))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_all_downloads(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM downloads ORDER BY created_at DESC;
        """)
        return [dict(r) for r in cur.fetchall()]

    def get_queue_items(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM downloads
            WHERE status IN ('QUEUED', 'DOWNLOADING', 'CONVERTING', 'PAUSED')
            ORDER BY created_at ASC;
        """)
        return [dict(r) for r in cur.fetchall()]

    def get_history_items(self, search_query: str = "") -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        if search_query:
            param = f"%{search_query.strip()}%"
            cur.execute("""
                SELECT * FROM downloads
                WHERE (title LIKE ? OR url LIKE ?)
                ORDER BY created_at DESC;
            """, (param, param))
        else:
            cur.execute("""
                SELECT * FROM downloads
                ORDER BY created_at DESC;
            """)
        return [dict(r) for r in cur.fetchall()]

    def get_download(self, item_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM downloads WHERE id = ?;", (item_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def delete_download(self, item_id: str) -> bool:
        conn = self._get_connection()
        with conn:
            conn.execute("DELETE FROM downloads WHERE id = ?;", (item_id,))
        return True

    def clear_completed(self):
        conn = self._get_connection()
        with conn:
            conn.execute("DELETE FROM downloads WHERE status = 'COMPLETED';")

    def reset_interrupted_to_paused(self):
        """When app boots up, convert any stale 'DOWNLOADING' or 'CONVERTING' state to 'PAUSED'"""
        conn = self._get_connection()
        with conn:
            conn.execute("""
                UPDATE downloads
                SET status = 'PAUSED', speed = 0.0, eta = 0
                WHERE status IN ('DOWNLOADING', 'CONVERTING', 'ANALYZING');
            """)

    def get_setting(self, key: str, default: Any = None) -> Any:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?;", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: Any):
        conn = self._get_connection()
        with conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?);", (key, str(value)))

    def close(self):
        """Closes the current thread's connection and resets singleton."""
        with self._lock:
            if hasattr(self._local, "conn") and self._local.conn is not None:
                try:
                    self._local.conn.close()
                except Exception:
                    pass
                self._local.conn = None
            Database._instance = None
