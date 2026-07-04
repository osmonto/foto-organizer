"""Generación y cacheado de thumbnails para la galería UI (F-24).

Por ahora solo genera thumbnails de fotos: los vídeos requerirían extraer un
fotograma vía ffmpeg, que no se puede verificar de forma fiable sin un
binario ``ffmpeg`` instalado; queda fuera de alcance de esta iteración.
"""

import hashlib
from pathlib import Path

from loguru import logger
from PIL import Image

from foto_organizer.core.scanner import MediaFile, MediaType

THUMBNAIL_SIZE = (256, 256)


def _cache_key(path: Path) -> str:
    """Clave de cache basada en ruta + mtime + tamaño.

    Invalida el cache automáticamente si el archivo cambia.
    """
    stat = path.stat()
    raw = f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def thumbnail_path(source_path: Path, cache_dir: Path) -> Path:
    """Ruta donde debería vivir (o ya vive) el thumbnail cacheado de ``source_path``."""
    return cache_dir / f"{_cache_key(source_path)}.jpg"


def get_or_create_thumbnail(media_file: MediaFile, cache_dir: Path) -> Path | None:
    """Devuelve la ruta de un thumbnail 256x256 de ``media_file``, usando cache.

    Si ya existe un thumbnail cacheado para ese archivo (misma ruta, mtime y
    tamaño) lo reutiliza sin regenerarlo. Devuelve ``None`` si no es una foto
    o si no se pudo generar (p. ej. archivo corrupto).
    """
    if media_file.media_type is not MediaType.PHOTO:
        return None

    cache_dir.mkdir(parents=True, exist_ok=True)
    target = thumbnail_path(media_file.path, cache_dir)
    if target.is_file():
        return target

    try:
        with Image.open(media_file.path) as image:
            rgb_image = image.convert("RGB")
            rgb_image.thumbnail(THUMBNAIL_SIZE)
            rgb_image.save(target, format="JPEG")
    except OSError as exc:
        logger.warning("No se pudo generar thumbnail de {}: {}", media_file.path, exc)
        return None

    return target
