"""Tests del diálogo de verificación pre-borrado (F-34)."""

from PySide6.QtWidgets import QAbstractButton, QDialogButtonBox
from pytestqt.qtbot import QtBot

from foto_organizer.core.verifier import VerificationResult, VerificationStatus
from foto_organizer.ui.verification_dialog import VerificationDialog

_OK_RESULTS = [
    VerificationResult("orig1", "backup1", VerificationStatus.OK),
    VerificationResult("orig2", "backup2", VerificationStatus.OK),
]
_MISMATCH_RESULTS = [
    VerificationResult("orig1", "backup1", VerificationStatus.HASH_MISMATCH),
]


def _ok_button(dialog: VerificationDialog) -> QAbstractButton:
    button = dialog._buttons.button(QDialogButtonBox.StandardButton.Ok)
    assert button is not None
    return button


def test_ok_button_disabled_initially(qtbot: QtBot) -> None:
    dialog = VerificationDialog(_OK_RESULTS)
    qtbot.addWidget(dialog)

    assert not _ok_button(dialog).isEnabled()


def test_ok_button_enabled_only_when_checkbox_and_phrase_match(qtbot: QtBot) -> None:
    dialog = VerificationDialog(_OK_RESULTS)
    qtbot.addWidget(dialog)

    dialog._review_checkbox.setChecked(True)
    assert not _ok_button(dialog).isEnabled()

    dialog._confirmation_edit.setText("CONFIRMAR")
    assert _ok_button(dialog).isEnabled()


def test_ok_button_stays_disabled_when_results_not_fully_verified(qtbot: QtBot) -> None:
    dialog = VerificationDialog(_MISMATCH_RESULTS)
    qtbot.addWidget(dialog)

    dialog._review_checkbox.setChecked(True)
    dialog._confirmation_edit.setText("CONFIRMAR")

    assert not _ok_button(dialog).isEnabled()


def test_wrong_confirmation_phrase_keeps_button_disabled(qtbot: QtBot) -> None:
    dialog = VerificationDialog(_OK_RESULTS)
    qtbot.addWidget(dialog)

    dialog._review_checkbox.setChecked(True)
    dialog._confirmation_edit.setText("confirmar")

    assert not _ok_button(dialog).isEnabled()
