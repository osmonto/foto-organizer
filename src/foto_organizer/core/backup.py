"""Copia segura de archivos a un directorio de backup, con manifiesto (F-12).

Regla de oro: nunca se mueve el original, siempre se copia (``shutil.copy2``).
"""

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from foto_organizer.core.scanner import MediaFile, scan_directory
from foto_organizer.utils.hasher import compute_hashes

MANIFEST_FILENAME = "backup_manifest.json"


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    """Una entrada del manifiesto: qué se copió, a dónde, y su hash de origen."""

    original_path: str
    backup_path: str
    md5: str
    sha256: str
    size_bytes: int
    backed_up_at: str


def run_backup(source: Path, destination: Path) -> list[ManifestEntry]:
    """Copia todas las fotos/vídeos de ``source`` a ``destination``.

    Preserva la estructura relativa de directorios y escribe
    ``backup_manifest.json`` en ``destination``. Nunca borra ni modifica
    nada en ``source``.
    """
    if source.resolve() == destination.resolve():
        raise ValueError("El directorio de backup no puede ser el mismo que el origen")

    media_files = scan_directory(source)
    destination.mkdir(parents=True, exist_ok=True)

    entries = [
        _backup_one(media_file, source, destination) for media_file in media_files
    ]

    _write_manifest(entries, destination)
    logger.info(
        "Backup completado: {} archivo(s) copiado(s) a {}", len(entries), destination
    )
    return entries


def _backup_one(
    media_file: MediaFile, source: Path, destination: Path
) -> ManifestEntry:
    relative_path = media_file.path.relative_to(source)
    backup_path = destination / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(media_file.path, backup_path)
    hashes = compute_hashes(media_file.path)

    return ManifestEntry(
        original_path=str(media_file.path),
        backup_path=str(backup_path),
        md5=hashes.md5,
        sha256=hashes.sha256,
        size_bytes=media_file.size_bytes,
        backed_up_at=datetime.now(UTC).isoformat(),
    )


def _write_manifest(entries: list[ManifestEntry], destination: Path) -> None:
    manifest_path = destination / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps([asdict(entry) for entry in entries], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_manifest(destination: Path) -> list[ManifestEntry]:
    """Carga un manifiesto previamente escrito por :func:`run_backup`."""
    manifest_path = destination / MANIFEST_FILENAME
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [ManifestEntry(**entry) for entry in data]
