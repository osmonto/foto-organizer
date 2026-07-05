"""Tests del diálogo de configuración (F-36)."""

import pytest
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


def test_browse_backup_dir_updates_field(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog

    dialog = SettingsDialog(AppSettings())
    qtbot.addWidget(dialog)
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *a, **k: "/nuevo/backup"),
    )

    dialog._browse_backup_dir()

    assert dialog._backup_dir_edit.text() == "/nuevo/backup"


def test_browse_backup_dir_cancelled_keeps_field(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog

    dialog = SettingsDialog(AppSettings(default_backup_dir="/original"))
    qtbot.addWidget(dialog)
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: "")
    )

    dialog._browse_backup_dir()

    assert dialog._backup_dir_edit.text() == "/original"
