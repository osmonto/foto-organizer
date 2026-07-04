"""Tests de la ventana principal (F-30/F-31): construcción y validación de dirs."""

from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from foto_organizer.ui.main_window import MainWindow


def test_main_window_builds_without_error(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "Organizador de Fotos y Vídeos"
    assert len(window.menuBar().actions()) == 3


def test_scan_source_populates_gallery(qtbot: QtBot, tmp_path: Path) -> None:
    from datetime import datetime

    from PIL import Image

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (100, 100), color="green").save(source / "foto.jpg")

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    window._scan_source()

    assert len(window._media_files) == 1
    assert window._gallery.item_count() == 1
    assert isinstance(window._media_files[0].modified_at, datetime)


def test_choose_source_dir_rejects_same_as_backup_dir(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    window = MainWindow()
    qtbot.addWidget(window)
    window._backup_dir = tmp_path

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *a, **k: str(tmp_path)),
    )
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: None))

    window._choose_source_dir()

    assert window._source_dir is None
