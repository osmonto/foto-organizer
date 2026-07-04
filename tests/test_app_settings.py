"""Tests de persistencia de configuración (F-36)."""

from pathlib import Path

from foto_organizer.utils.app_settings import AppSettings, load_settings, save_settings


def test_load_settings_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    result = load_settings(tmp_path / "missing.json")

    assert result == AppSettings()


def test_save_then_load_settings_roundtrips(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    original = AppSettings(
        folder_format="YYYY-MM",
        included_extensions=[".jpg"],
        excluded_extensions=[".gif"],
        default_backup_dir=str(tmp_path / "backup"),
    )

    save_settings(original, settings_path)
    loaded = load_settings(settings_path)

    assert loaded == original
