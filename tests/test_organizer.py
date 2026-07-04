"""Tests de organización por fecha, duplicados y renombrado (F-43)."""

import json
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import IFD

from foto_organizer.core.organizer import (
    QUARANTINE_DIRNAME,
    apply_organization,
    build_duplicate_report,
    build_organized_filename,
    date_subdirectory,
    find_duplicates_by_hash,
    find_duplicates_by_name_and_size,
    plan_organization,
    quarantine_duplicates,
    resolve_capture_date,
    write_duplicate_report,
)
from foto_organizer.core.scanner import MediaFile, MediaType, scan_directory


def _photo_with_exif_date(path: Path, datetime_original: str) -> None:
    image = Image.new("RGB", (10, 10), color="green")
    exif = image.getexif()
    exif.get_ifd(IFD.Exif)[0x9003] = datetime_original
    image.save(path, format="JPEG", exif=exif)


def _media_file(path: Path, media_type: MediaType = MediaType.PHOTO) -> MediaFile:
    stat = path.stat()
    return MediaFile(
        path=path,
        media_type=media_type,
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )


def test_date_subdirectory_formats_year_month_name() -> None:
    result = date_subdirectory(datetime(2024, 3, 15))

    assert result == Path("2024") / "03-Marzo"


def test_build_organized_filename_uses_timestamp_prefix() -> None:
    result = build_organized_filename(datetime(2024, 3, 15, 10, 30, 5), "IMG_0001.jpg")

    assert result == "20240315_103005_IMG_0001.jpg"


def test_resolve_capture_date_prefers_exif_over_modified_at(tmp_path: Path) -> None:
    photo_path = tmp_path / "foto.jpg"
    _photo_with_exif_date(photo_path, "2020:01:01 00:00:00")
    media_file = _media_file(photo_path)

    captured_at = resolve_capture_date(media_file)

    assert captured_at == datetime(2020, 1, 1, 0, 0, 0)


def test_resolve_capture_date_falls_back_to_modified_at(tmp_path: Path) -> None:
    photo_path = tmp_path / "foto.jpg"
    Image.new("RGB", (10, 10), color="red").save(photo_path, format="JPEG")
    media_file = _media_file(photo_path)

    captured_at = resolve_capture_date(media_file)

    assert captured_at == media_file.modified_at


def test_plan_and_apply_organization_copies_into_date_structure(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    photo_path = source / "IMG_0001.jpg"
    _photo_with_exif_date(photo_path, "2024:03:15 10:30:00")

    media_files = scan_directory(source)
    destination = tmp_path / "organized"

    entries = plan_organization(media_files, destination)
    apply_organization(entries)

    expected = destination / "2024" / "03-Marzo" / "20240315_103000_IMG_0001.jpg"
    assert expected.is_file()
    assert photo_path.is_file()  # el original nunca se toca


def test_plan_organization_handles_filename_collisions(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "a").mkdir(parents=True)
    (source / "b").mkdir(parents=True)
    _photo_with_exif_date(source / "a" / "IMG_0001.jpg", "2024:03:15 10:30:00")
    _photo_with_exif_date(source / "b" / "IMG_0001.jpg", "2024:03:15 10:30:00")

    media_files = scan_directory(source)
    destination = tmp_path / "organized"

    entries = plan_organization(media_files, destination)
    target_names = sorted(Path(e.target_path).name for e in entries)

    assert target_names == [
        "20240315_103000_IMG_0001.jpg",
        "20240315_103000_IMG_0001_01.jpg",
    ]


def test_find_duplicates_by_hash_groups_identical_content(tmp_path: Path) -> None:
    (tmp_path / "foto1.jpg").write_bytes(b"contenido-identico")
    (tmp_path / "foto2.jpg").write_bytes(b"contenido-identico")
    (tmp_path / "foto3.jpg").write_bytes(b"contenido-distinto")

    media_files = scan_directory(tmp_path)
    groups = find_duplicates_by_hash(media_files)

    assert len(groups) == 1
    assert {Path(p).name for p in groups[0].paths} == {"foto1.jpg", "foto2.jpg"}


def test_find_duplicates_by_name_and_size_is_a_fast_heuristic(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "IMG_0001.jpg").write_bytes(b"1234")
    (tmp_path / "b" / "IMG_0001.jpg").write_bytes(
        b"5678"
    )  # mismo nombre/tamaño, distinto contenido

    media_files = scan_directory(tmp_path)
    groups = find_duplicates_by_name_and_size(media_files)

    assert len(groups) == 1
    assert len(groups[0].paths) == 2


def test_quarantine_duplicates_moves_files_preserving_relative_path(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    (source / "cumple").mkdir(parents=True)
    original = source / "cumple" / "IMG_0100_copia.jpg"
    original.write_bytes(b"contenido-identico")

    moved = quarantine_duplicates([str(original)], source)

    expected = source / QUARANTINE_DIRNAME / "cumple" / "IMG_0100_copia.jpg"
    assert moved == [expected]
    assert expected.is_file()
    assert not original.exists()


def test_build_and_write_duplicate_report(tmp_path: Path) -> None:
    (tmp_path / "foto1.jpg").write_bytes(b"contenido-identico")
    (tmp_path / "foto2.jpg").write_bytes(b"contenido-identico")

    media_files = scan_directory(tmp_path)
    report = build_duplicate_report(media_files)
    report_path = write_duplicate_report(report, tmp_path)

    assert report_path.is_file()
    raw = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(raw["confirmed_by_hash"]) == 1
