"""Vista de galería: grid de thumbnails con selección y vista previa (F-32)."""

from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from foto_organizer.core.scanner import MediaFile
from foto_organizer.utils.thumbnails import get_or_create_thumbnail

_GRID_ICON_SIZE = QSize(200, 200)
_PATH_ROLE = Qt.ItemDataRole.UserRole


class ImagePreviewDialog(QDialog):
    """Diálogo modal con la vista previa ampliada de un archivo."""

    def __init__(self, path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(path.name)

        label = QLabel()
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            label.setPixmap(
                pixmap.scaled(
                    800,
                    800,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            label.setText(f"Sin vista previa disponible para {path.name}")

        layout = QVBoxLayout(self)
        layout.addWidget(label)


class GalleryView(QWidget):
    """Grid scrolleable de thumbnails con selección múltiple y vista previa."""

    selection_changed = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._list = QListWidget()
        self._list.setViewMode(QListWidget.ViewMode.IconMode)
        self._list.setIconSize(_GRID_ICON_SIZE)
        self._list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._list.setSpacing(8)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list)

    def set_media_files(
        self, media_files: Sequence[MediaFile], cache_dir: Path
    ) -> None:
        """Rellena la galería con un thumbnail por cada archivo de ``media_files``."""
        self._list.clear()
        for media_file in media_files:
            item = QListWidgetItem(media_file.path.name)
            item.setData(_PATH_ROLE, str(media_file.path))
            thumbnail = get_or_create_thumbnail(media_file, cache_dir)
            if thumbnail is not None:
                item.setIcon(_icon_from_path(thumbnail))
            self._list.addItem(item)

    def selected_paths(self) -> list[Path]:
        """Rutas de los archivos actualmente seleccionados en la galería."""
        return [Path(item.data(_PATH_ROLE)) for item in self._list.selectedItems()]

    def item_count(self) -> int:
        return self._list.count()

    def _on_selection_changed(self) -> None:
        self.selection_changed.emit(self.selected_paths())

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        path = Path(item.data(_PATH_ROLE))
        dialog = ImagePreviewDialog(path, self)
        dialog.exec()


def _icon_from_path(path: Path) -> QIcon:
    return QIcon(QPixmap(str(path)))
