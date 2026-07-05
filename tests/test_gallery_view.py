"""Tests de la vista de galería (F-32)."""

from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from foto_organizer.core.scanner import MediaFile, MediaType
from foto_organizer.ui.gallery_view import GalleryView, ImagePreviewDialog


def _make_photo(directory: Path, name: str = "foto.jpg") -> MediaFile:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    Image.new("RGB", (200, 150), color="red").save(path, format="JPEG")
    stat = path.stat()
    return MediaFile(
        path=path,
        media_type=MediaType.PHOTO,
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )


def test_set_media_files_populates_items(qtbot: QtBot, tmp_path: Path) -> None:
    gallery = GalleryView()
    qtbot.addWidget(gallery)
    media_files = [
        _make_photo(tmp_path / "source", "a.jpg"),
        _make_photo(tmp_path / "source", "b.jpg"),
    ]

    gallery.set_media_files(media_files, tmp_path / "cache")

    assert gallery.item_count() == 2


def test_selection_changed_signal_reports_selected_paths(
    qtbot: QtBot, tmp_path: Path
) -> None:
    gallery = GalleryView()
    qtbot.addWidget(gallery)
    media_file = _make_photo(tmp_path / "source", "a.jpg")
    gallery.set_media_files([media_file], tmp_path / "cache")

    gallery._list.item(0).setSelected(True)

    assert gallery.selected_paths() == [media_file.path]


def test_preview_dialog_shows_pixmap_for_valid_image(
    qtbot: QtBot, tmp_path: Path
) -> None:
    media_file = _make_photo(tmp_path / "source")

    dialog = ImagePreviewDialog(media_file.path)
    qtbot.addWidget(dialog)

    label = dialog.findChild(QLabel)
    assert isinstance(label, QLabel)
    assert not label.pixmap().isNull()


def test_preview_dialog_falls_back_to_text_for_unreadable_file(
    qtbot: QtBot, tmp_path: Path
) -> None:
    broken = tmp_path / "roto.jpg"
    broken.write_bytes(b"esto no es una imagen")

    dialog = ImagePreviewDialog(broken)
    qtbot.addWidget(dialog)

    label = dialog.findChild(QLabel)
    assert isinstance(label, QLabel)
    assert "Sin vista previa disponible" in label.text()


def test_double_click_opens_preview_dialog(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[str] = []
    monkeypatch.setattr(
        ImagePreviewDialog, "exec", lambda self: opened.append(self.windowTitle())
    )
    gallery = GalleryView()
    qtbot.addWidget(gallery)
    media_file = _make_photo(tmp_path / "source", "a.jpg")
    gallery.set_media_files([media_file], tmp_path / "cache")

    gallery._on_item_double_clicked(gallery._list.item(0))

    assert opened == ["a.jpg"]
