"""Configuración centralizada de logging con loguru.

Todos los módulos importan ``logger`` directamente de loguru; este módulo
solo configura los sinks (consola + archivo rotativo). El log de auditoría
de borrados (Fase 1) usará un sink separado con ``filter``.
"""

import sys
from pathlib import Path

from loguru import logger

DEFAULT_LOG_DIR = Path.home() / ".foto_organizer" / "logs"

CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan> - <level>{message}</level>"
)
FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} - {message}"


def setup_logging(log_dir: Path = DEFAULT_LOG_DIR, console_level: str = "INFO") -> None:
    """Configura los sinks de loguru para toda la aplicación.

    Debe llamarse una única vez al arrancar. En consola se muestra
    ``console_level`` o superior; el archivo guarda siempre DEBUG.
    """
    logger.remove()
    logger.add(sys.stderr, level=console_level, format=CONSOLE_FORMAT)

    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "foto_organizer_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        format=FILE_FORMAT,
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )
