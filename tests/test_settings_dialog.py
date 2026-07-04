"""Tests del diálogo de configuración (F-36)."""

from pytestqt.qtbot import QtBot

from foto_organizer.ui.settings_dialog import SettingsDialog
from foto_organizer.utils.app_settings import AppSettings


def test_settings_dialog_prefills_from_existing_settings(qtbot: QtBot) -> None:
    initial = AppSettings(
        folder_format="YYYY/MM",
        included_extensions=[".jpg"],
        excluded_extensions=[".gif"],
        default_backup_dir="/tmp/backup",
    )
    dialog = SettingsDialog(initial)
    qtbot.addWidget(dialog)

    assert dialog.settings() == initial


def test_settings_dialog_returns_edited_values(qtbot: QtBot) -> None:
    dialog = SettingsDialog(AppSettings())
    qtbot.addWidget(dialog)

    dialog._folder_format_edit.setText("YYYY-MM")
    dialog._included_extensions_edit.setText(".jpg, .png")
    dialog._excluded_extensions_edit.setText(".raw")
    dialog._backup_dir_edit.setText("/backups")

    result = dialog.settings()

    assert result.folder_format == "YYYY-MM"
    assert result.included_extensions == [".jpg", ".png"]
    assert result.excluded_extensions == [".raw"]
    assert result.default_backup_dir == "/backups"
