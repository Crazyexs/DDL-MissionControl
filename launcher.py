# launcher.py — minimal runnable entry point

import os, sys
from PyQt5.QtWidgets import QApplication
from ddl import MainWindow  # provided by ddl/__init__.py re-export

if __name__ == "__main__":
    # run from project root (helps with relative files like config.json)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # High-DPI friendliness (optional; safe if unsupported)
    try:
        from PyQt5.QtCore import Qt
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    app = QApplication(sys.argv)
    win = MainWindow()  # builds UI, wires managers
    sys.exit(app.exec())
