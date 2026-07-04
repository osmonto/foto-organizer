"""Tests de extracción de metadata EXIF/vídeo (F-20)."""

from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import IFD

from foto_organizer.core.scanner import MediaType
from foto_organizer.utils.metadata import extract_metadata


def _make_photo_with_exif(
    path: Path,
    *,
    datetime_original: str | None = None,
    model: str | None = None,
    gps: tuple[tuple[float, float, float], str, tuple[float, float, float], str]
    | None = None,
) -> None:
    image = Image.new("RGB", (10, 10), color="red")
    exif = image.getexif()
    if model is not None:
        exif[0x0110] = model
    if datetime_original is not None:
        exif.get_ifd(IFD.Exif)[0x9003] = datetime_original
    if gps is not None:
        lat_dms, lat_ref, lon_dms, lon_ref = gps
        gps_ifd = exif.get_ifd(IFD.GPSInfo)
        gps_ifd[1] = lat_ref
        gps_ifd[2] = lat_dms
        gps_ifd[3] = lon_ref
        gps_ifd[4] = lon_dms
    image.save(path, format="JPEG", exif=exif)


def test_extract_metadata_reads_datetime_original_and_model(tmp_path: Path) -> None:
    photo_path = tmp_path / "foto.jpg"
    _make_photo_with_exif(
        photo_path, datetime_original="2024:03:15 10:30:00", model="TestCamera"
    )

    metadata = extract_metadata(photo_path, MediaType.PHOTO)

    assert metadata.captured_at == datetime(2024, 3, 15, 10, 30, 0)
    assert metadata.camera_model == "TestCamera"


def test_extract_metadata_reads_gps_coordinates(tmp_path: Path) -> None:
    photo_path = tmp_path / "foto.jpg"
    _make_photo_with_exif(
        photo_path,
        gps=((40.0, 26.0, 46.0), "N", (74.0, 0.0, 21.0), "W"),
    )

    metadata = extract_metadata(photo_path, MediaType.PHOTO)

    assert metadata.gps is not None
    assert metadata.gps.latitude == 40.0 + 26.0 / 60 + 46.0 / 3600
    assert metadata.gps.longitude == -(74.0 + 0.0 / 60 + 21.0 / 3600)


def test_extract_metadata_returns_none_fields_without_exif(tmp_path: Path) -> None:
    photo_path = tmp_path / "foto.jpg"
    Image.new("RGB", (10, 10), color="blue").save(photo_path, format="JPEG")

    metadata = extract_metadata(photo_path, MediaType.PHOTO)

    assert metadata.captured_at is None
    assert metadata.camera_model is None
    assert metadata.gps is None


def test_extract_metadata_video_falls_back_gracefully_without_ffprobe(
    tmp_path: Path,
) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"no es un mp4 real")

    metadata = extract_metadata(video_path, MediaType.VIDEO)

    assert metadata.duration_seconds is None
    assert metadata.captured_at is None
