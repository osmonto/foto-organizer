"""Vista de duplicados: grupos con selección manual de cuál conservar (F-35)."""

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from foto_organizer.core.organizer import DuplicateGroup, DuplicateReport


class DuplicatesDialog(QDialog):
    """Muestra los grupos de duplicados y deja elegir, por grupo, qué archivo conservar.

    Solo se listan los duplicados confirmados por hash (``confirmed_by_hash``):
    son coincidencias de contenido exacto, no la heurística de nombre+tamaño.
    """

    def __init__(self, report: DuplicateReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Duplicados encontrados")
        self.resize(600, 500)

        self._groups = report.confirmed_by_hash
        self._button_groups: list[QButtonGroup] = []

        content = QWidget()
        content_layout = QVBoxLayout(content)

        if not self._groups:
            content_layout.addWidget(QLabel("No se encontraron duplicados."))
        for group in self._groups:
            content_layout.addWidget(self._build_group_box(group))
        content_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        layout.addWidget(buttons)

    def _build_group_box(self, group: DuplicateGroup) -> QGroupBox:
        box = QGroupBox(f"Grupo {group.key[:12]}… ({len(group.paths)} archivos)")
        box_layout = QVBoxLayout(box)
        button_group = QButtonGroup(box)
        button_group.setExclusive(True)
        for index, path in enumerate(group.paths):
            radio = QRadioButton(path)
            radio.setProperty("path", path)
            if index == 0:
                radio.setChecked(True)
            button_group.addButton(radio)
            box_layout.addWidget(radio)
        self._button_groups.append(button_group)
        return box

    def paths_to_remove(self) -> list[str]:
        """Rutas que el usuario NO marcó para conservar en cada grupo."""
        to_remove: list[str] = []
        for group, button_group in zip(self._groups, self._button_groups, strict=True):
            checked = button_group.checkedButton()
            kept_path = checked.property("path") if checked is not None else None
            to_remove.extend(path for path in group.paths if path != kept_path)
        return to_remove
