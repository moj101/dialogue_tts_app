# -*- coding: utf-8 -*-
"""
توابع کمکی رابط کاربری و استایل.
"""

from pathlib import Path
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyle

from config import BASE_DIR


def load_app_icon() -> QIcon:
    """
    بارگذاری آیکون اصلی برنامه در صورت وجود فایل.
    """
    candidates = [
        BASE_DIR / "app_icon.ico",
        BASE_DIR / "app_icon.png",
        BASE_DIR / "assets" / "app_icon.ico",
        BASE_DIR / "assets" / "app_icon.png",
    ]

    for path in candidates:
        if Path(path).exists():
            return QIcon(str(path))

    app = QApplication.instance()
    if app:
        return app.style().standardIcon(QStyle.SP_ComputerIcon)
    return QIcon()


def get_standard_icon(pixmap_name: int) -> QIcon:
    """
    دریافت آیکون استاندارد Qt.
    """
    app = QApplication.instance()
    if not app:
        return QIcon()
    return app.style().standardIcon(pixmap_name)


def app_stylesheet() -> str:
    """
    استایل کلی برنامه.
    """
    return """
    QWidget {
        font-family: Tahoma;
        font-size: 11pt;
    }

    QMainWindow, QDialog {
        background-color: #f4f7fb;
    }

    QGroupBox {
        background-color: #ffffff;
        border: 1px solid #d9e2ef;
        border-radius: 12px;
        margin-top: 12px;
        padding: 12px;
        font-weight: bold;
        color: #203040;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        right: 12px;
        padding: 0 8px 0 8px;
        color: #284b7a;
    }

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDoubleSpinBox, QTableWidget {
        background-color: #ffffff;
        border: 1px solid #c9d6e8;
        border-radius: 8px;
        padding: 6px;
        selection-background-color: #3b82f6;
        selection-color: white;
    }

    QTextEdit, QPlainTextEdit {
        padding: 8px;
    }

    QPushButton {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 14px;
        min-height: 18px;
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #1d4ed8;
    }

    QPushButton:pressed {
        background-color: #1e40af;
    }

    QPushButton:disabled {
        background-color: #9db7ea;
        color: #eaf1ff;
    }

    QTableWidget {
        gridline-color: #e5edf8;
        alternate-background-color: #f8fbff;
    }

    QHeaderView::section {
        background-color: #eaf2ff;
        color: #203040;
        padding: 6px;
        border: none;
        border-bottom: 1px solid #d4e0f2;
        font-weight: bold;
    }

    QMenuBar {
        background-color: #ffffff;
        border-bottom: 1px solid #dde6f3;
    }

    QMenuBar::item {
        padding: 8px 12px;
        background: transparent;
    }

    QMenuBar::item:selected {
        background: #eaf2ff;
        border-radius: 6px;
    }

    QMenu {
        background-color: white;
        border: 1px solid #dce6f5;
        padding: 6px;
    }

    QMenu::item {
        padding: 8px 24px 8px 24px;
        border-radius: 6px;
    }

    QMenu::item:selected {
        background-color: #eaf2ff;
    }

    QLabel {
        color: #1f2937;
    }

    QProgressBar {
        background-color: #e8eef8;
        border: none;
        border-radius: 8px;
        text-align: center;
        min-height: 18px;
    }

    QProgressBar::chunk {
        background-color: #22c55e;
        border-radius: 8px;
    }

    QTableWidget::item {
        padding: 4px;
    }
    """