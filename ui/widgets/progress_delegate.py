"""
StreamBatch - Custom Table Delegates and Cell Formatters
Renders progress bars, badges, and humanized data units.
"""
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle, QApplication
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import Qt, QRect

def format_bytes(bytes_count: float) -> str:
    """Formats raw bytes into human readable KB, MB, GB."""
    if not bytes_count or bytes_count <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_count) < 1024.0:
            return f"{bytes_count:3.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"

def format_speed(bytes_per_sec: float) -> str:
    """Formats download speed into KB/s or MB/s."""
    if not bytes_per_sec or bytes_per_sec <= 0:
        return "--"
    return f"{format_bytes(bytes_per_sec)}/s"

def format_eta(seconds: int) -> str:
    """Formats remaining seconds into mm:ss or hh:mm:ss."""
    if not seconds or seconds <= 0:
        return "--"
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

def format_duration(seconds: int) -> str:
    """Formats video/audio duration."""
    if not seconds or seconds <= 0:
        return "--:--"
    m = seconds // 60
    s = seconds % 60
    if m >= 60:
        h = m // 60
        m = m % 60
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class ProgressBarDelegate(QStyledItemDelegate):
    """
    Renders a sleek in-table progress bar showing percent and downloaded / total size.
    """
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Background fill on selection
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#1e3a5f"))
        else:
            painter.fillRect(option.rect, QColor("#14161d") if index.row() % 2 == 0 else QColor("#181b24"))

        data = index.data(Qt.UserRole)
        # Expecting dict: {"percent": float, "downloaded": int, "total": int, "status": str}
        if not data or not isinstance(data, dict):
            painter.restore()
            super().paint(painter, option, index)
            return

        percent = data.get("percent", 0.0)
        status = data.get("status", "QUEUED")

        rect = option.rect.adjusted(6, 6, -6, -6)

        # Bar background
        bg_rect = QRect(rect.left(), rect.top() + 4, rect.width(), 14)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#1f2430"))
        painter.drawRoundedRect(bg_rect, 4, 4)

        # Chunk progress
        if status == "COMPLETED":
            chunk_width = bg_rect.width()
            painter.setBrush(QColor("#10b981")) # emerald green
            painter.drawRoundedRect(bg_rect, 4, 4)
        elif status == "DOWNLOADING" and percent > 0:
            chunk_width = int(bg_rect.width() * (min(100.0, max(0.0, percent)) / 100.0))
            if chunk_width > 0:
                chunk_rect = QRect(bg_rect.left(), bg_rect.top(), chunk_width, bg_rect.height())
                painter.setBrush(QColor("#0078d4"))
                painter.drawRoundedRect(chunk_rect, 4, 4)
        elif status == "CONVERTING":
            # Striped/amber converting indicator
            chunk_width = bg_rect.width()
            painter.setBrush(QColor("#8b5cf6")) # purple
            painter.drawRoundedRect(bg_rect, 4, 4)
        elif status == "ERROR":
            chunk_width = bg_rect.width()
            painter.setBrush(QColor("#ef4444"))
            painter.drawRoundedRect(bg_rect, 4, 4)

        # Text percentage & bytes
        text_rect = QRect(rect.left(), rect.bottom() - 14, rect.width(), 14)
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor("#cbd5e1"))

        if status == "COMPLETED":
            size_str = format_bytes(data.get("total", 0) or data.get("downloaded", 0))
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"100% ({size_str})")
        elif status == "DOWNLOADING":
            dl_str = format_bytes(data.get("downloaded", 0))
            tot_str = format_bytes(data.get("total", 0))
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{percent:.1f}% ({dl_str} / {tot_str})")
        elif status == "CONVERTING":
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, "Converting audio...")
        elif status == "PAUSED":
            dl_str = format_bytes(data.get("downloaded", 0))
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"Paused ({dl_str})")
        elif status == "ERROR":
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, "Failed")
        else:
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, "Queued")

        painter.restore()


class StatusBadgeDelegate(QStyledItemDelegate):
    """
    Renders status as a modern badge pill (e.g. DOWNLOADING, COMPLETED, PAUSED, ERROR).
    """
    COLORS = {
        "COMPLETED": {"bg": "#064e3b", "fg": "#34d399", "border": "#059669"},
        "DOWNLOADING": {"bg": "#1e3a8a", "fg": "#60a5fa", "border": "#2563eb"},
        "CONVERTING": {"bg": "#4c1d95", "fg": "#c084fc", "border": "#7c3aed"},
        "QUEUED": {"bg": "#374151", "fg": "#9ca3af", "border": "#4b5563"},
        "PAUSED": {"bg": "#78350f", "fg": "#fbbf24", "border": "#d97706"},
        "ERROR": {"bg": "#7f1d1d", "fg": "#f87171", "border": "#dc2626"},
        "CANCELLED": {"bg": "#374151", "fg": "#9ca3af", "border": "#4b5563"}
    }

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Background fill on selection
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#1e3a5f"))
        else:
            painter.fillRect(option.rect, QColor("#14161d") if index.row() % 2 == 0 else QColor("#181b24"))

        status_text = index.data(Qt.DisplayRole) or "QUEUED"
        style = self.COLORS.get(status_text.upper(), self.COLORS["QUEUED"])

        # Draw Badge Pill
        badge_rect = option.rect.adjusted(8, 10, -8, -10)
        if badge_rect.height() < 16:
            badge_rect = option.rect.adjusted(4, 4, -4, -4)

        painter.setPen(QColor(style["border"]))
        painter.setBrush(QColor(style["bg"]))
        painter.drawRoundedRect(badge_rect, 4, 4)

        painter.setPen(QColor(style["fg"]))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(badge_rect, Qt.AlignCenter, status_text.upper())

        painter.restore()
