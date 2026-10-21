"""
StreamBatch - Modern Dark Theme Stylesheet (QSS)
Clean, modern dark theme inspired by professional desktop download utilities.
"""

DARK_THEME_QSS = """
/* Base Window & Dialog */
QMainWindow, QDialog {
    background-color: #1a1c23;
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* ToolBar & Action Bar */
QToolBar {
    background-color: #13151b;
    border-bottom: 1px solid #2d3748;
    spacing: 8px;
    padding: 6px 12px;
}

QToolButton {
    background-color: #242936;
    color: #f7fafc;
    border: 1px solid #3b4252;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
}

QToolButton:hover {
    background-color: #2e3440;
    border-color: #0084ff;
    color: #ffffff;
}

QToolButton:pressed {
    background-color: #1e222b;
}

/* Push Buttons */
QPushButton {
    background-color: #2b303c;
    color: #f7fafc;
    border: 1px solid #3e4451;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #383f4f;
    border-color: #0084ff;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1e222b;
}

QPushButton:disabled {
    background-color: #1e222b;
    border-color: #2b303c;
    color: #64748b;
}

QPushButton#primaryBtn {
    background-color: #0078d4;
    border: 1px solid #0084ff;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#primaryBtn:hover {
    background-color: #1084d8;
    border-color: #339af0;
}

QPushButton#dangerBtn {
    background-color: #c53030;
    border: 1px solid #e53e3e;
    color: #ffffff;
}

QPushButton#dangerBtn:hover {
    background-color: #e53e3e;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #2d3748;
    background-color: #1a1c23;
    top: -1px;
}

QTabBar::tab {
    background-color: #13151b;
    color: #94a3b8;
    padding: 10px 22px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #242936;
    border-bottom: none;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #1a1c23;
    color: #00a8ff;
    border-color: #2d3748;
    border-bottom: 2px solid #00a8ff;
}

QTabBar::tab:hover:!selected {
    background-color: #21252f;
    color: #e2e8f0;
}

/* Table Widget */
QTableWidget {
    background-color: #14161d;
    alternate-background-color: #181b24;
    color: #e2e8f0;
    gridline-color: #232733;
    border: 1px solid #2d3748;
    border-radius: 6px;
    selection-background-color: #1e3a5f;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #13151b;
    color: #94a3b8;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #242936;
    border-bottom: 1px solid #2d3748;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
}

/* Inputs & Combos */
QLineEdit, QComboBox, QSpinBox {
    background-color: #12141a;
    border: 1px solid #363d4d;
    border-radius: 6px;
    color: #ffffff;
    padding: 6px 10px;
    selection-background-color: #0078d4;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #0084ff;
    background-color: #161820;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left-width: 0px;
}

QComboBox QAbstractItemView {
    background-color: #1a1c23;
    color: #e2e8f0;
    border: 1px solid #363d4d;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #2d3748;
    border-radius: 4px;
    background-color: #12141a;
    text-align: center;
    color: #f7fafc;
    font-size: 11px;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d4, stop:1 #00c0ff);
    border-radius: 3px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #14161d;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #363d4d;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #4b5563;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #111318;
    border-top: 1px solid #232733;
    color: #94a3b8;
    font-size: 12px;
}

QStatusBar QLabel {
    color: #94a3b8;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #2d3748;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 16px;
    font-weight: bold;
    color: #cbd5e1;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    background-color: #1a1c23;
}

/* Badges and Warnings */
QLabel#warningBadge {
    background-color: #432b08;
    color: #f6ad55;
    border: 1px solid #744210;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}

QLabel#infoBadge {
    background-color: #1a365d;
    color: #63b3ed;
    border: 1px solid #2b6cb0;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}
"""
