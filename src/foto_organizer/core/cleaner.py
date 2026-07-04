"""Borrado seguro del origen, solo tras verificación 100% OK (F-14).

Reglas irrompibles aplicadas aquí:
- Nunca se borra si algún archivo no está en estado ``OK``.
- Requiere la frase de confirmación exacta ``"CONFIRMAR"`` (la UI añade,
  en F-34, una segunda confirmación mediante checkbox).
- Cada borrado queda registrado en el log de auditoría con timestamp.
"""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from foto_organizer.core.verifier import VerificationResult, is_fully_verified

CONFIRMATION_PHRASE = "CONFIRMAR"


class DeletionNotAuthorizedError(Exception):
    """El borrado fue rechazado: falta confirmación o hay archivos sin verificar OK."""


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Un registro de auditoría de un borrado individual."""

    original_path: str
    backup_path: str
    deleted_at: str


def delete_verified_sources(
    results: list[VerificationResult],
    *,
    confirmation_phrase: str,
    audit_log_path: Path,
) -> list[AuditRecord]:
    """Borra los archivos origen de ``results``, solo si todos están verificados OK.

    ``confirmation_phrase`` debe ser exactamente ``CONFIRMATION_PHRASE``. Levanta
    :class:`DeletionNotAuthorizedError` sin borrar nada si falta la confirmación
    o si algún archivo no está verificado como ``OK``.
    """
    if confirmation_phrase != CONFIRMATION_PHRASE:
        raise DeletionNotAuthorizedError(
            f'Se requiere escribir "{CONFIRMATION_PHRASE}" para confirmar el borrado'
        )
    if not is_fully_verified(results):
        raise DeletionNotAuthorizedError(
            "No se puede borrar: hay archivos sin verificar o con estado distinto de OK"
        )

    records = [_delete_one(result) for result in results]
    _append_audit_log(records, audit_log_path)
    logger.info(
        "Borrado seguro completado: {} archivo(s) eliminado(s) del origen", len(records)
    )
    return records


def _delete_one(result: VerificationResult) -> AuditRecord:
    original = Path(result.original_path)
    original.unlink()
    logger.info("Original borrado tras verificación: {}", original)
    return AuditRecord(
        original_path=result.original_path,
        backup_path=result.backup_path,
        deleted_at=datetime.now(UTC).isoformat(),
    )


def _append_audit_log(records: list[AuditRecord], audit_log_path: Path) -> None:
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_log_path.open("a", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
