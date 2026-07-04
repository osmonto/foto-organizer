"""Punto de entrada: ``python -m foto_organizer``."""

from loguru import logger

from foto_organizer import __version__
from foto_organizer.utils.logger import setup_logging


def main() -> None:
    setup_logging()
    logger.info("foto-organizer v{} - la UI llega en la Fase 3", __version__)


if __name__ == "__main__":
    main()
