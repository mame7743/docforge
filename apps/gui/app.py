import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow

from .main_view import MainView
from .main_controller import MainController


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DocForge")

    window = QMainWindow()
    window.setWindowTitle("DocForge — Document to Knowledge Base")
    window.resize(800, 700)

    view = MainView()
    controller = MainController(view)
    window.setCentralWidget(view)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
