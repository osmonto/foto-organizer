"""Tests del borrado seguro de originales (F-14)."""

from pathlib import Path

import pytest

from foto_organizer.core.backup import run_backup
from foto_organizer.core.cleaner import (
    CONFIRMATION_PHRASE,
    DeletionNotAuthorizedError,
    delete_verified_sources,
)
from foto_organizer.core.verifier import VerificationResult, verify_backup


def _verified_backup(tmp_path: Path) -> tuple[Path, list[VerificationResult]]:
    source = tmp_path / "source"
    destination = tmp_path / "backup"
    source.mkdir()
    (source / "foto.jpg").write_bytes(b"contenido-original")
    entries = run_backup(source, destination)
    results = verify_backup(entries)
    return source, results


def test_delete_verified_sources_removes_original_when_ok(tmp_path: Path) -> None:
    source, results = _verified_backup(tmp_path)
    audit_log = tmp_path / "audit.log"

    records = delete_verified_sources(
        results, confirmation_phrase=CONFIRMATION_PHRASE, audit_log_path=audit_log
    )

    assert not (source / "foto.jpg").exists()
    assert len(records) == 1


def test_delete_verified_sources_writes_audit_log(tmp_path: Path) -> None:
    source, results = _verified_backup(tmp_path)
    audit_log = tmp_path / "audit.log"

    delete_verified_sources(
        results, confirmation_phrase=CONFIRMATION_PHRASE, audit_log_path=audit_log
    )

    lines = audit_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert "foto.jpg" in lines[0]


def test_delete_verified_sources_rejects_wrong_confirmation_phrase(
    tmp_path: Path,
) -> None:
    source, results = _verified_backup(tmp_path)
    audit_log = tmp_path / "audit.log"

    with pytest.raises(DeletionNotAuthorizedError):
        delete_verified_sources(
            results, confirmation_phrase="si, borralo", audit_log_path=audit_log
        )

    assert (source / "foto.jpg").exists()
    assert not audit_log.exists()


def test_delete_verified_sources_rejects_when_not_fully_verified(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "backup"
    source.mkdir()
    (source / "foto.jpg").write_bytes(b"contenido-original")
    entries = run_backup(source, destination)
    (destination / "foto.jpg").write_bytes(b"corrupto")  # simula backup dañado
    results = verify_backup(entries)
    audit_log = tmp_path / "audit.log"

    with pytest.raises(DeletionNotAuthorizedError):
        delete_verified_sources(
            results, confirmation_phrase=CONFIRMATION_PHRASE, audit_log_path=audit_log
        )

    assert (source / "foto.jpg").exists()
