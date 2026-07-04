"""Extracción de metadata EXIF (fotos) y de duración (vídeos) — F-20."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import ffmpeg
import pillow_heif
from loguru import logger
from PIL import Image
from PIL.ExifTags import GPSTAGS, IFD

from foto_organizer.core.scanner import MediaType

pillow_heif.register_heif_opener()

_DATETIME_ORIGINAL_TAG = 0x9003
_MODEL_TAG = 0x0110
_EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"


@dataclass(frozen=True, slots=True)
class GPSCoordinates:
    """Coordenadas GPS en grados decimales."""

    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class MediaMetadata:
    """Metadata extraída de una foto o vídeo. Todos los campos son opcionales."""

    captured_at: datetime | None
    camera_model: str | None
    gps: GPSCoordinates | None
    duration_seconds: float | None


_EMPTY_METADATA = MediaMetadata(
    captured_at=None, camera_model=None, gps=None, duration_seconds=None
)


def extract_metadata(path: Path, media_type: MediaType) -> MediaMetadata:
    """Extrae la metadata disponible de ``path`` según su tipo (foto o vídeo)."""
    if media_type is MediaType.PHOTO:
        return _extract_photo_metadata(path)
    return _extract_video_metadata(path)


def _extract_photo_metadata(path: Path) -> MediaMetadata:
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            if not exif:
                return _EMPTY_METADATA

            camera_model = exif.get(_MODEL_TAG)

            captured_at = None
            exif_ifd = exif.get_ifd(IFD.Exif)
            raw_datetime = exif_ifd.get(_DATETIME_ORIGINAL_TAG)
            if raw_datetime:
                captured_at = _parse_exif_datetime(str(raw_datetime))

            gps = _extract_gps(exif.get_ifd(IFD.GPSInfo))
    except (OSError, SyntaxError) as exc:
        logger.warning("No se pudo leer EXIF de {}: {}", path, exc)
        return _EMPTY_METADATA

    return MediaMetadata(
        captured_at=captured_at,
        camera_model=str(camera_model) if camera_model else None,
        gps=gps,
        duration_seconds=None,
    )


def _parse_exif_datetime(raw: str) -> datetime | None:
    try:
        return datetime.strptime(raw, _EXIF_DATETIME_FORMAT)
    except ValueError:
        return None


def _dms_to_decimal(dms: tuple[float, float, float], ref: str) -> float:
    # Los valores de PIL vienen como IFDRational: se convierten a float para
    # que el resultado sea un float real, no un Fraction de precisión exacta.
    degrees, minutes, seconds = (float(x) for x in dms)
    decimal = degrees + minutes / 60 + seconds / 3600
    return -decimal if ref in ("S", "W") else decimal


def _extract_gps(gps_ifd: dict[int, Any]) -> GPSCoordinates | None:
    if not gps_ifd:
        return None

    tagged: dict[str, Any] = {GPSTAGS.get(k, str(k)): v for k, v in gps_ifd.items()}
    latitude_dms = tagged.get("GPSLatitude")
    longitude_dms = tagged.get("GPSLongitude")
    if latitude_dms is None or longitude_dms is None:
        return None

    latitude = _dms_to_decimal(
        tuple(latitude_dms), str(tagged.get("GPSLatitudeRef", "N"))
    )
    longitude = _dms_to_decimal(
        tuple(longitude_dms), str(tagged.get("GPSLongitudeRef", "E"))
    )
    return GPSCoordinates(latitude=latitude, longitude=longitude)


def _extract_video_metadata(path: Path) -> MediaMetadata:
    try:
        probe = ffmpeg.probe(str(path))
    except (ffmpeg.Error, FileNotFoundError) as exc:
        logger.warning(
            "No se pudo leer metadata de vídeo (¿falta ffprobe?) en {}: {}", path, exc
        )
        return _EMPTY_METADATA

    duration_raw = probe.get("format", {}).get("duration")
    duration_seconds = float(duration_raw) if duration_raw is not None else None

    return MediaMetadata(
        captured_at=None,
        camera_model=None,
        gps=None,
        duration_seconds=duration_seconds,
    )
