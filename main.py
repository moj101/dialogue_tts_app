# -*- coding: utf-8 -*-
"""
نقطه ورود برنامه.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ui_main import MainWindow
from resources import app_stylesheet, load_app_icon


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setApplicationName("نرم‌افزار تولید صدای گفتگو")
    app.setStyleSheet(app_stylesheet())

    icon = load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()