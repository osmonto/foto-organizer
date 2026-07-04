"""Configuración persistente de la app, editable desde ``settings_dialog`` (F-36)."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from foto_organizer.core.scanner import PHOTO_EXTENSIONS, VIDEO_EXTENSIONS

DEFAULT_SETTINGS_PATH = Path.home() / ".foto_organizer" / "settings.json"
DEFAULT_FOLDER_FORMAT = "YYYY/MM-NombreMes"
DEFAULT_BACKUP_DIR = Path.home() / "foto_organizer_backups"


@dataclass(slots=True)
class AppSettings:
    """Preferencias de organización, persistidas en disco como JSON."""

    folder_format: str = DEFAULT_FOLDER_FORMAT
    included_extensions: list[str] = field(
        default_factory=lambda: sorted(PHOTO_EXTENSIONS | VIDEO_EXTENSIONS)
    )
    excluded_extensions: list[str] = field(default_factory=list)
    default_backup_dir: str = str(DEFAULT_BACKUP_DIR)


def load_settings(settings_path: Path = DEFAULT_SETTINGS_PATH) -> AppSettings:
    """Carga la config desde ``settings_path``; usa valores por defecto si falta."""
    if not settings_path.is_file():
        return AppSettings()

    data = json.loads(settings_path.read_text(encoding="utf-8"))
    return AppSettings(**data)


def save_settings(
    settings: AppSettings, settings_path: Path = DEFAULT_SETTINGS_PATH
) -> None:
    """Guarda ``settings`` como JSON en ``settings_path``."""
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(asdict(settings), indent=2, ensure_ascii=False), encoding="utf-8"
    )
