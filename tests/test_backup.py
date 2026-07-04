"""Tests del sistema de backup seguro (F-40)."""

import json
from pathlib import Path

import pytest

from foto_organizer.core.backup import MANIFEST_FILENAME, load_manifest, run_backup
from foto_organizer.utils.hasher import compute_hashes


def test_run_backup_copies_files_preserving_content(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "backup"
    source.mkdir()
    (source / "foto.jpg").write_bytes(b"contenido-original")

    entries = run_backup(source, destination)

    assert len(entries) == 1
    assert (destination / "foto.jpg").read_bytes() == b"contenido-original"


def test_run_backup_preserves_relative_directory_structure(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "backup"
    (source / "2024" / "marzo").mkdir(parents=True)
    (source / "2024" / "marzo" / "foto.jpg").write_bytes(b"data")

    run_backup(source, destination)

    assert (destination / "2024" / "marzo" / "foto.jpg").is_file()


def test_run_backup_never_modifies_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "backup"
    source.mkdir()
    original_file = source / "foto.jpg"
    original_file.write_bytes(b"contenido-original")

    run_backup(source, destination)

    assert original_file.read_bytes() == b"contenido-original"
    assert list(source.iterdir()) == [original_file]


def test_run_backup_writes_valid_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "backup"
    source.mkdir()
    (source / "foto.jpg").write_bytes(b"contenido-original")

    entries = run_backup(source, destination)

    manifest_path = destination / MANIFEST_FILENAME
    assert manifest_path.is_file()

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(raw) == 1
    assert raw[0]["original_path"] == entries[0].original_path
    assert raw[0]["sha256"] == compute_hashes(source / "foto.jpg").sha256


def test_load_manifest_roundtrip(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "backup"
    source.mkdir()
    (source / "foto.jpg").write_bytes(b"contenido-original")

    entries = run_backup(source, destination)
    loaded = load_manifest(destination)

    assert loaded == entries


def test_run_backup_rejects_same_source_and_destination(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(ValueError, match="mismo"):
        run_backup(source, source)
