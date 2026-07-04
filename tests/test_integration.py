"""Tests de integración de los flujos completos (F-44)."""

from pathlib import Path

from foto_organizer.core.backup import run_backup
from foto_organizer.core.organizer import (
    apply_organization,
    build_duplicate_report,
    find_duplicates_by_hash,
    plan_organization,
)
from foto_organizer.core.scanner import scan_directory
from foto_organizer.core.verifier import (
    VerificationStatus,
    is_fully_verified,
    verify_backup,
    write_verification_report,
)


def test_full_flow_scan_backup_verify_does_not_delete_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    backup_destination = tmp_path / "backup"
    (source / "2024").mkdir(parents=True)
    (source / "2024" / "foto.jpg").write_bytes(b"contenido-original")
    (source / "video.mp4").write_bytes(b"contenido-video")

    media_files = scan_directory(source)
    assert len(media_files) == 2

    backup_entries = run_backup(source, backup_destination)
    assert len(backup_entries) == 2

    results = verify_backup(backup_entries)
    assert is_fully_verified(results)
    assert all(result.status is VerificationStatus.OK for result in results)

    report_path = write_verification_report(results, backup_destination)
    assert report_path.is_file()

    # El origen nunca se toca: ni el flujo de backup ni el de verificación borran nada.
    assert (source / "2024" / "foto.jpg").read_bytes() == b"contenido-original"
    assert (source / "video.mp4").read_bytes() == b"contenido-video"


def test_full_flow_with_duplicates_detects_and_organizes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    backup_destination = tmp_path / "backup"
    organized_destination = tmp_path / "organized"
    source.mkdir()
    (source / "foto1.jpg").write_bytes(b"contenido-identico")
    (source / "foto2.jpg").write_bytes(b"contenido-identico")
    (source / "foto3.jpg").write_bytes(b"contenido-unico")

    media_files = scan_directory(source)
    assert len(media_files) == 3

    duplicate_groups = find_duplicates_by_hash(media_files)
    assert len(duplicate_groups) == 1
    assert {Path(p).name for p in duplicate_groups[0].paths} == {
        "foto1.jpg",
        "foto2.jpg",
    }

    report = build_duplicate_report(media_files)
    assert len(report.confirmed_by_hash) == 1

    backup_entries = run_backup(source, backup_destination)
    results = verify_backup(backup_entries)
    assert is_fully_verified(results)

    organization_entries = plan_organization(media_files, organized_destination)
    apply_organization(organization_entries)

    organized_files = sorted(
        path.name for path in organized_destination.rglob("*") if path.is_file()
    )
    assert len(organized_files) == 3
    for name in ("foto1.jpg", "foto2.jpg", "foto3.jpg"):
        assert any(organized.endswith(name) for organized in organized_files)
