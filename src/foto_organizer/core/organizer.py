"""Organización de archivos: por fecha, duplicados y renombrado (F-21/22/23).

Al igual que ``backup.py``, esto solo copia — nunca mueve ni borra nada del
origen.
"""

import json
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from foto_organizer.core.scanner import MediaFile
from foto_organizer.utils.hasher import compute_hashes
from foto_organizer.utils.metadata import extract_metadata

DUPLICATE_REPORT_FILENAME = "duplicates_report.json"

_MONTHS_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


# --- F-21: organización por fecha ------------------------------------------------


def date_subdirectory(captured_at: datetime) -> Path:
    """Construye ``YYYY/MM-NombreMes`` (p. ej. ``2024/03-Marzo``)."""
    month_name = _MONTHS_ES[captured_at.month]
    return Path(f"{captured_at.year:04d}") / f"{captured_at.month:02d}-{month_name}"


def resolve_capture_date(media_file: MediaFile) -> datetime:
    """Fecha EXIF (``DateTimeOriginal``) si existe; si no, fecha de modificación."""
    metadata = extract_metadata(media_file.path, media_file.media_type)
    return metadata.captured_at or media_file.modified_at


# --- F-23: renombrado automático ---------------------------------------------------


def build_organized_filename(captured_at: datetime, original_name: str) -> str:
    """Construye ``YYYYMMDD_HHMMSS_original_name.ext``."""
    timestamp = captured_at.strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{original_name}"


def _unique_target_path(directory: Path, filename: str, reserved: set[Path]) -> Path:
    """Añade sufijos ``_01``, ``_02``... si ``filename`` ya está ocupado.

    Comprueba tanto el disco como ``reserved`` (rutas ya planeadas en el
    mismo lote, que todavía no existen físicamente).
    """
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    candidate = directory / filename
    counter = 1
    while candidate.exists() or candidate in reserved:
        candidate = directory / f"{stem}_{counter:02d}{suffix}"
        counter += 1
    reserved.add(candidate)
    return candidate


# --- Plan y ejecución de la organización --------------------------------------------


@dataclass(frozen=True, slots=True)
class OrganizeEntry:
    """Un movimiento planeado: archivo origen -> destino organizado por fecha."""

    source_path: str
    target_path: str


def plan_organization(
    media_files: Sequence[MediaFile], destination_root: Path
) -> list[OrganizeEntry]:
    """Calcula la ruta destino organizada por fecha de cada archivo.

    Solo calcula el plan; no copia nada. Las colisiones de nombre (incluidas
    las que ocurren dentro del propio lote) se resuelven con sufijos.
    """
    reserved: set[Path] = set()
    entries = []
    for media_file in media_files:
        captured_at = resolve_capture_date(media_file)
        subdirectory = destination_root / date_subdirectory(captured_at)
        filename = build_organized_filename(captured_at, media_file.path.name)
        target = _unique_target_path(subdirectory, filename, reserved)
        entries.append(
            OrganizeEntry(source_path=str(media_file.path), target_path=str(target))
        )
    return entries


def apply_organization(entries: Sequence[OrganizeEntry]) -> None:
    """Copia cada archivo de origen a su destino organizado. Nunca mueve nada."""
    for entry in entries:
        target = Path(entry.target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry.source_path, target)
    logger.info("Organización aplicada: {} archivo(s) copiado(s)", len(entries))


# --- F-22: detección de duplicados ---------------------------------------------------


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    """Un grupo de archivos que coinciden según un criterio de duplicado."""

    key: str
    paths: list[str]


@dataclass(frozen=True, slots=True)
class DuplicateReport:
    """Reporte de duplicados, generado antes de que el usuario actúe sobre ellos."""

    generated_at: str
    confirmed_by_hash: list[DuplicateGroup]
    heuristic_by_name_and_size: list[DuplicateGroup]


def find_duplicates_by_hash(media_files: Sequence[MediaFile]) -> list[DuplicateGroup]:
    """Agrupa archivos con contenido idéntico, comparando SHA256.

    Para evitar hashear toda la biblioteca, primero agrupa por tamaño
    (barato) y solo calcula el hash de los archivos que comparten tamaño
    con al menos otro archivo.
    """
    by_size: dict[int, list[MediaFile]] = {}
    for media_file in media_files:
        by_size.setdefault(media_file.size_bytes, []).append(media_file)

    by_hash: dict[str, list[Path]] = {}
    for candidates in by_size.values():
        if len(candidates) < 2:
            continue
        for media_file in candidates:
            sha256 = compute_hashes(media_file.path).sha256
            by_hash.setdefault(sha256, []).append(media_file.path)

    return [
        DuplicateGroup(key=sha256, paths=[str(p) for p in paths])
        for sha256, paths in by_hash.items()
        if len(paths) > 1
    ]


def find_duplicates_by_name_and_size(
    media_files: Sequence[MediaFile],
) -> list[DuplicateGroup]:
    """Agrupa archivos por nombre + tamaño: heurística rápida, sin leer contenido."""
    groups: dict[tuple[str, int], list[Path]] = {}
    for media_file in media_files:
        key = (media_file.path.name, media_file.size_bytes)
        groups.setdefault(key, []).append(media_file.path)

    return [
        DuplicateGroup(key=f"{name}|{size}", paths=[str(p) for p in paths])
        for (name, size), paths in groups.items()
        if len(paths) > 1
    ]


def build_duplicate_report(media_files: Sequence[MediaFile]) -> DuplicateReport:
    """Genera el reporte de duplicados combinando ambos criterios."""
    return DuplicateReport(
        generated_at=datetime.now(UTC).isoformat(),
        confirmed_by_hash=find_duplicates_by_hash(media_files),
        heuristic_by_name_and_size=find_duplicates_by_name_and_size(media_files),
    )


def write_duplicate_report(report: DuplicateReport, destination: Path) -> Path:
    """Escribe ``duplicates_report.json`` en ``destination`` y devuelve su ruta."""
    report_path = destination / DUPLICATE_REPORT_FILENAME
    payload = {
        "generated_at": report.generated_at,
        "confirmed_by_hash": [
            {"sha256": g.key, "paths": g.paths} for g in report.confirmed_by_hash
        ],
        "heuristic_by_name_and_size": [
            {"name_and_size": g.key, "paths": g.paths}
            for g in report.heuristic_by_name_and_size
        ],
    }
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report_path
