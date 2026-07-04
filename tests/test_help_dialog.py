"""Tests de la guía de uso (menú Ayuda)."""

from PySide6.QtWidgets import QTextBrowser
from pytestqt.qtbot import QtBot

from foto_organizer.ui.help_dialog import HelpDialog


def test_help_dialog_shows_non_empty_guide(qtbot: QtBot) -> None:
    dialog = HelpDialog()
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Guía de uso"
    browser = dialog.findChild(QTextBrowser)
    assert browser is not None
    assert "Escanear origen" in browser.toPlainText()
    assert "CONFIRMAR" in browser.toPlainText()
