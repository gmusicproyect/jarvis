"""Estilos Qt — graphite + ámbar (mayordomo ejecutivo)."""

JARVIS_QSS = """
QWidget {
    background-color: #1a1d23;
    color: #e8eaed;
    font-family: "SF Pro Text", "Helvetica Neue", "Segoe UI", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #1a1d23;
}
QTabWidget::pane {
    border: 1px solid #2c313a;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background: #242830;
    color: #9aa0a6;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background: #2c313a;
    color: #f0c75e;
}
QPushButton {
    background-color: #2c313a;
    border: 1px solid #3d4450;
    border-radius: 6px;
    padding: 8px 14px;
    color: #e8eaed;
}
QPushButton:hover {
    background-color: #3a404c;
    border-color: #f0c75e;
}
QPushButton#primary {
    background-color: #c9a227;
    color: #1a1d23;
    font-weight: 600;
    border: none;
}
QPushButton#primary:hover {
    background-color: #f0c75e;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {
    background-color: #12141a;
    border: 1px solid #3d4450;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: #c9a227;
}
QLabel#title {
    font-size: 22px;
    font-weight: 700;
    color: #f0c75e;
}
QLabel#subtitle {
    color: #9aa0a6;
}
QLabel#ok { color: #6bcf7f; }
QLabel#bad { color: #e57373; }
QGroupBox {
    border: 1px solid #2c313a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #f0c75e;
}
QListWidget, QTableWidget {
    background-color: #12141a;
    border: 1px solid #2c313a;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #242830;
    color: #9aa0a6;
    border: none;
    padding: 6px;
}
QStatusBar {
    background: #12141a;
    color: #9aa0a6;
}
QScrollBar:vertical {
    background: #1a1d23;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #3d4450;
    border-radius: 4px;
    min-height: 24px;
}
"""
