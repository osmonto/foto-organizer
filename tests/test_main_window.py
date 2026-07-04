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


def test_find_duplicates_populates_gallery_even_without_prior_scan(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image

    from foto_organizer.ui.duplicates_dialog import DuplicatesDialog

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (100, 100), color="green").save(source / "foto.jpg")

    monkeypatch.setattr(DuplicatesDialog, "exec", lambda self: None)

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    # Regresión: ir directo a "Buscar duplicados" sin pasar antes por
    # "Escanear origen" debía dejar la galería vacía (F-32 solo se refrescaba
    # desde _scan_source), aunque _media_files sí se poblara.
    window._find_duplicates()

    assert len(window._media_files) == 1
    assert window._gallery.item_count() == 1


def test_find_duplicates_accepted_quarantines_unselected_duplicates(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image
    from PySide6.QtWidgets import QMessageBox

    from foto_organizer.core.organizer import QUARANTINE_DIRNAME
    from foto_organizer.ui.duplicates_dialog import DuplicatesDialog

    source = tmp_path / "source"
    source.mkdir()
    kept = source / "foto1.jpg"
    duplicate = source / "foto2.jpg"
    Image.new("RGB", (100, 100), color="green").save(kept)
    Image.new("RGB", (100, 100), color="green").save(duplicate)

    monkeypatch.setattr(
        DuplicatesDialog, "exec", lambda self: DuplicatesDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(
        DuplicatesDialog, "paths_to_remove", lambda self: [str(duplicate)]
    )
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    window._find_duplicates()

    assert not duplicate.exists()
    assert (source / QUARANTINE_DIRNAME / "foto2.jpg").is_file()
    assert kept.is_file()


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
