"""Tests de verificación de integridad del backup (F-41)."""

from pathlib import Path

from foto_organizer.core.backup import run_backup
from foto_organizer.core.verifier import (
    VerificationStatus,
    is_fully_verified,
    verify_backup,
    write_verification_report,
)


def _make_backup(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    destination = tmp_path / "backup"
    source.mkdir()
    (source / "foto.jpg").write_bytes(b"contenido-original")
    return source, destination


def test_verify_backup_reports_ok_for_intact_files(tmp_path: Path) -> None:
    source, destination = _make_backup(tmp_path)
    entries = run_backup(source, destination)

    results = verify_backup(entries)

    assert len(results) == 1
    assert results[0].status is VerificationStatus.OK
    assert is_fully_verified(results)


def test_verify_backup_detects_hash_mismatch(tmp_path: Path) -> None:
    source, destination = _make_backup(tmp_path)
    entries = run_backup(source, destination)

    (destination / "foto.jpg").write_bytes(b"contenido-corrupto")

    results = verify_backup(entries)

    assert results[0].status is VerificationStatus.HASH_MISMATCH
    assert not is_fully_verified(results)


def test_verify_backup_detects_missing_file(tmp_path: Path) -> None:
    source, destination = _make_backup(tmp_path)
    entries = run_backup(source, destination)

    (destination / "foto.jpg").unlink()

    results = verify_backup(entries)

    assert results[0].status is VerificationStatus.MISSING
    assert not is_fully_verified(results)


def test_write_verification_report_creates_json_file(tmp_path: Path) -> None:
    source, destination = _make_backup(tmp_path)
    entries = run_backup(source, destination)
    results = verify_backup(entries)

    report_path = write_verification_report(results, destination)

    assert report_path.is_file()


def test_is_fully_verified_is_false_for_empty_results() -> None:
    assert is_fully_verified([]) is False
