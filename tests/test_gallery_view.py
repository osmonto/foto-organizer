"""Tests de la vista de galería (F-32)."""

from datetime import datetime
from pathlib import Path

from PIL import Image
from pytestqt.qtbot import QtBot

from foto_organizer.core.scanner import MediaFile, MediaType
from foto_organizer.ui.gallery_view import GalleryView


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
