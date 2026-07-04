"""Escaneo de directorios en busca de fotos y vídeos (F-10)."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

PHOTO_EXTENSIONS = frozenset(
    {".jpg", ".jpeg", ".png", ".heic", ".raw", ".dng", ".tiff"}
)
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".avi", ".mkv", ".m4v"})


class MediaType(Enum):
    """Tipo de archivo multimedia detectado."""

    PHOTO = "photo"
    VIDEO = "video"


@dataclass(frozen=True, slots=True)
class MediaFile:
    """Un archivo de foto/vídeo encontrado durante el escaneo."""

    path: Path
    media_type: MediaType
    size_bytes: int
    modified_at: datetime


def _media_type_for(extension: str) -> MediaType | None:
    ext = extension.lower()
    if ext in PHOTO_EXTENSIONS:
        return MediaType.PHOTO
    if ext in VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    return None


def scan_directory(source: Path) -> list[MediaFile]:
    """Escanea recursivamente ``source`` y devuelve las fotos/vídeos encontrados.

    ``source`` se trata como solo lectura: nunca se escribe ni se borra nada.
    Los archivos con extensión no reconocida se ignoran en silencio.
    """
    if not source.is_dir():
        raise NotADirectoryError(f"El directorio fuente no existe: {source}")

    return list(_iter_media_files(source))


def _iter_media_files(source: Path) -> Iterator[MediaFile]:
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        media_type = _media_type_for(path.suffix)
        if media_type is None:
            continue
        stat = path.stat()
        yield MediaFile(
            path=path,
            media_type=media_type,
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )
