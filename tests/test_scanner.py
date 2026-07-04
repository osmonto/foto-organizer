"""Tests de escaneo de directorios (F-42)."""

from pathlib import Path

import pytest

from foto_organizer.core.scanner import MediaType, scan_directory


def test_scan_directory_detects_photos_and_videos(tmp_path: Path) -> None:
    (tmp_path / "foto.jpg").write_bytes(b"fake-jpg")
    (tmp_path / "video.mp4").write_bytes(b"fake-mp4")
    (tmp_path / "notas.txt").write_text("no es multimedia")

    results = scan_directory(tmp_path)

    by_name = {f.path.name: f for f in results}
    assert set(by_name) == {"foto.jpg", "video.mp4"}
    assert by_name["foto.jpg"].media_type is MediaType.PHOTO
    assert by_name["video.mp4"].media_type is MediaType.VIDEO


def test_scan_directory_is_recursive(tmp_path: Path) -> None:
    nested = tmp_path / "2024" / "marzo"
    nested.mkdir(parents=True)
    (nested / "foto.heic").write_bytes(b"fake-heic")

    results = scan_directory(tmp_path)

    assert len(results) == 1
    assert results[0].path == nested / "foto.heic"


def test_scan_directory_handles_empty_directory(tmp_path: Path) -> None:
    assert scan_directory(tmp_path) == []


def test_scan_directory_ignores_files_without_extension(tmp_path: Path) -> None:
    (tmp_path / "archivo_sin_extension").write_bytes(b"contenido")

    assert scan_directory(tmp_path) == []


def test_scan_directory_raises_for_missing_source(tmp_path: Path) -> None:
    missing = tmp_path / "no_existe"

    with pytest.raises(NotADirectoryError):
        scan_directory(missing)
