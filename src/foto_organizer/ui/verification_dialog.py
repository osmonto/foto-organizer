"""Diálogo de verificación pre-borrado: exige revisión y confirmación (F-34)."""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from foto_organizer.core.cleaner import CONFIRMATION_PHRASE
from foto_organizer.core.verifier import VerificationResult, VerificationStatus


class VerificationDialog(QDialog):
    """Muestra el reporte de verificación y exige doble confirmación antes de borrar.

    El botón de confirmación solo se habilita cuando: (1) todos los archivos
    están en estado ``OK``, (2) el usuario marcó el checkbox de revisión, y
    (3) escribió exactamente la frase de confirmación (``CONFIRMAR``).
    """

    def __init__(
        self, results: list[VerificationResult], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Confirmar borrado del origen")
        self._all_ok = len(results) > 0 and all(
            r.status is VerificationStatus.OK for r in results
        )

        table = _build_report_table(results)

        self._review_checkbox = QCheckBox("He revisado el reporte completo")
        self._review_checkbox.toggled.connect(self._update_confirm_state)

        self._confirmation_edit = QLineEdit()
        self._confirmation_edit.setPlaceholderText(
            f'Escribe "{CONFIRMATION_PHRASE}" para confirmar'
        )
        self._confirmation_edit.textChanged.connect(self._update_confirm_state)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        if not self._all_ok:
            layout.addWidget(
                QLabel(
                    "No se puede borrar: hay archivos sin verificar o con"
                    " estado distinto de OK."
                )
            )
        layout.addWidget(table)
        layout.addWidget(self._review_checkbox)
        layout.addWidget(self._confirmation_edit)
        layout.addWidget(self._buttons)

        self._update_confirm_state()

    def confirmation_phrase(self) -> str:
        return self._confirmation_edit.text()

    def _update_confirm_state(self) -> None:
        ready = (
            self._all_ok
            and self._review_checkbox.isChecked()
            and self._confirmation_edit.text() == CONFIRMATION_PHRASE
        )
        ok_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setEnabled(ready)


def _build_report_table(results: list[VerificationResult]) -> QTableWidget:
    table = QTableWidget(len(results), 3)
    table.setHorizontalHeaderLabels(["Original", "Backup", "Estado"])
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    header = table.horizontalHeader()
    if header is not None:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    for row, result in enumerate(results):
        table.setItem(row, 0, QTableWidgetItem(result.original_path))
        table.setItem(row, 1, QTableWidgetItem(result.backup_path))
        table.setItem(row, 2, QTableWidgetItem(result.status.value))
    return table
