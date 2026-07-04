"""Punto de entrada: ``python -m foto_organizer``."""

import sys

from loguru import logger
from PySide6.QtWidgets import QApplication

from foto_organizer import __version__
from foto_organizer.ui.main_window import MainWindow
from foto_organizer.utils.logger import setup_logging


def main() -> None:
    setup_logging()
    logger.info("foto-organizer v{}", __version__)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
