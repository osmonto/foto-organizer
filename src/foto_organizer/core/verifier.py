"""Verificación de integridad del backup: hash origen vs. destino (F-13).

Esta es la comprobación que habilita el borrado seguro (F-14), así que
recalcula ambos hashes en el momento en vez de confiar en valores cacheados
del manifiesto.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from loguru import logger

from foto_organizer.core.backup import ManifestEntry
from foto_organizer.utils.hasher import compute_hashes

VERIFICATION_REPORT_FILENAME = "verification_report.json"


class VerificationStatus(Enum):
    """Resultado de comparar un archivo origen con su copia de backup."""

    OK = "OK"
    HASH_MISMATCH = "HASH_MISMATCH"
    MISSING = "MISSING"


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Resultado de verificación para una entrada del manifiesto."""

    original_path: str
    backup_path: str
    status: VerificationStatus


def verify_backup(manifest: list[ManifestEntry]) -> list[VerificationResult]:
    """Verifica cada entrada del manifiesto comparando hash origen vs. destino."""
    return [_verify_one(entry) for entry in manifest]


def _verify_one(entry: ManifestEntry) -> VerificationResult:
    original = Path(entry.original_path)
    backup = Path(entry.backup_path)

    if not backup.is_file() or not original.is_file():
        logger.warning(
            "Archivo faltante durante verificación: {} / {}", original, backup
        )
        return VerificationResult(
            entry.original_path, entry.backup_path, VerificationStatus.MISSING
        )

    original_hashes = compute_hashes(original)
    backup_hashes = compute_hashes(backup)

    if original_hashes != backup_hashes:
        logger.error("Hash mismatch entre origen y backup: {} vs {}", original, backup)
        return VerificationResult(
            entry.original_path, entry.backup_path, VerificationStatus.HASH_MISMATCH
        )

    return VerificationResult(
        entry.original_path, entry.backup_path, VerificationStatus.OK
    )


def is_fully_verified(results: list[VerificationResult]) -> bool:
    """True si y solo si todos los resultados son OK.

    Un listado vacío nunca se considera verificado, para evitar falsos
    positivos si el borrado se invoca sin haber verificado nada antes.
    """
    return len(results) > 0 and all(r.status is VerificationStatus.OK for r in results)


def _result_to_dict(result: VerificationResult) -> dict[str, str]:
    return {
        "original_path": result.original_path,
        "backup_path": result.backup_path,
        "status": result.status.value,
    }


def write_verification_report(
    results: list[VerificationResult], destination: Path
) -> Path:
    """Escribe ``verification_report.json`` en ``destination`` y devuelve su ruta."""
    report_path = destination / VERIFICATION_REPORT_FILENAME
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "fully_verified": is_fully_verified(results),
        "total_files": len(results),
        "results": [_result_to_dict(r) for r in results],
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report_path
