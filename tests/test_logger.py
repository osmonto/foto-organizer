"""Tests de la configuración de logging (F-07)."""

from pathlib import Path

from loguru import logger

from foto_organizer.utils.logger import setup_logging


def test_setup_logging_creates_log_dir(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"

    setup_logging(log_dir=log_dir)

    assert log_dir.is_dir()


def test_setup_logging_writes_to_file(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    setup_logging(log_dir=log_dir)

    logger.debug("mensaje de prueba")
    logger.remove()  # cierra los sinks para vaciar el buffer en Windows

    log_files = list(log_dir.glob("*.log"))
    assert len(log_files) == 1
    assert "mensaje de prueba" in log_files[0].read_text(encoding="utf-8")
