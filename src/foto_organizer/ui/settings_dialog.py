"""Pantalla de configuración: carpetas, extensiones, backup por defecto (F-36)."""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from foto_organizer.utils.app_settings import AppSettings


class SettingsDialog(QDialog):
    """Diálogo modal para editar :class:`AppSettings`."""

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configuración")

        self._folder_format_edit = QLineEdit(settings.folder_format)
        self._included_extensions_edit = QLineEdit(
            ", ".join(settings.included_extensions)
        )
        self._excluded_extensions_edit = QLineEdit(
            ", ".join(settings.excluded_extensions)
        )
        self._backup_dir_edit = QLineEdit(settings.default_backup_dir)

        browse_button = QPushButton("Examinar…")
        browse_button.clicked.connect(self._browse_backup_dir)
        backup_dir_row = QHBoxLayout()
        backup_dir_row.addWidget(self._backup_dir_edit)
        backup_dir_row.addWidget(browse_button)
        backup_dir_row_widget = QWidget()
        backup_dir_row_widget.setLayout(backup_dir_row)

        form = QFormLayout()
        form.addRow("Formato de carpetas", self._folder_format_edit)
        form.addRow("Extensiones incluidas", self._included_extensions_edit)
        form.addRow("Extensiones excluidas", self._excluded_extensions_edit)
        form.addRow("Directorio de backup por defecto", backup_dir_row_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self.setLayout(form)

    def _browse_backup_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de backup", self._backup_dir_edit.text()
        )
        if directory:
            self._backup_dir_edit.setText(directory)

    def settings(self) -> AppSettings:
        """Construye un :class:`AppSettings` a partir del estado del formulario."""
        return AppSettings(
            folder_format=self._folder_format_edit.text().strip(),
            included_extensions=_split_extensions(
                self._included_extensions_edit.text()
            ),
            excluded_extensions=_split_extensions(
                self._excluded_extensions_edit.text()
            ),
            default_backup_dir=self._backup_dir_edit.text().strip(),
        )


def _split_extensions(raw: str) -> list[str]:
    return [ext.strip() for ext in raw.split(",") if ext.strip()]
