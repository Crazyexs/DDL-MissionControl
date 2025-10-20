import os, sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ddl import MainWindow

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    os.environ.setdefault("QT_FONT_DPI", "96")
    app = QApplication(sys.argv)
    win = MainWindow()
    sys.exit(app.exec())
