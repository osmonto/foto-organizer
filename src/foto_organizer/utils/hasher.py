"""Cálculo de hashes MD5 + SHA256 para verificación de integridad (F-11)."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

_CHUNK_SIZE = 1024 * 1024  # 1 MiB


@dataclass(frozen=True, slots=True)
class FileHashes:
    """Hashes de un archivo, usados para comparar origen vs. copia de backup."""

    md5: str
    sha256: str


def compute_hashes(path: Path) -> FileHashes:
    """Calcula MD5 y SHA256 de ``path`` en una sola pasada, leyendo por bloques."""
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with path.open("rb") as fh:
        while chunk := fh.read(_CHUNK_SIZE):
            md5.update(chunk)
            sha256.update(chunk)

    return FileHashes(md5=md5.hexdigest(), sha256=sha256.hexdigest())
