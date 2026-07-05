"""Tests de generación y cacheado de thumbnails (F-24)."""

from datetime import datetime
from pathlib import Path

from PIL import Image

from foto_organizer.core.scanner import MediaFile, MediaType
from foto_organizer.utils.thumbnails import THUMBNAIL_SIZE, get_or_create_thumbnail


def _make_photo(source_dir: Path, size: tuple[int, int] = (800, 600)) -> MediaFile:
    source_dir.mkdir(parents=True, exist_ok=True)
    photo_path = source_dir / "foto.jpg"
    Image.new("RGB", size, color="blue").save(photo_path, format="JPEG")
    stat = photo_path.stat()
    return MediaFile(
        path=photo_path,
        media_type=MediaType.PHOTO,
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )


def test_get_or_create_thumbnail_resizes_to_256_max(tmp_path: Path) -> None:
    media_file = _make_photo(tmp_path / "source", size=(800, 600))
    cache_dir = tmp_path / "cache"

    result = get_or_create_thumbnail(media_file, cache_dir)

    assert result is not None
    with Image.open(result) as thumb:
        assert max(thumb.size) == THUMBNAIL_SIZE[0]


def test_get_or_create_thumbnail_uses_cache_on_second_call(tmp_path: Path) -> None:
    media_file = _make_photo(tmp_path / "source")
    cache_dir = tmp_path / "cache"

    first = get_or_create_thumbnail(media_file, cache_dir)
    assert first is not None
    first.write_bytes(b"cache-corrupto-para-el-test")

    second = get_or_create_thumbnail(media_file, cache_dir)

    assert second == first
    assert second.read_bytes() == b"cache-corrupto-para-el-test"


def test_get_or_create_thumbnail_returns_none_for_video(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake-video-bytes")
    stat = video_path.stat()
    media_file = MediaFile(
        path=video_path,
        media_type=MediaType.VIDEO,
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )

    result = get_or_create_thumbnail(media_file, tmp_path / "cache")

    assert result is None


def test_get_or_create_thumbnail_returns_none_for_corrupt_photo(
    tmp_path: Path,
) -> None:
    photo_path = tmp_path / "roto.jpg"
    photo_path.write_bytes(b"esto no es un jpeg")
    stat = photo_path.stat()
    media_file = MediaFile(
        path=photo_path,
        media_type=MediaType.PHOTO,
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )

    result = get_or_create_thumbnail(media_file, tmp_path / "cache")

    assert result is None
