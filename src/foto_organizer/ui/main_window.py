"""Ventana principal de la aplicación (F-30/F-31/F-33)."""

from pathlib import Path

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QFileSystemModel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from foto_organizer.core.backup import MANIFEST_FILENAME, run_backup
from foto_organizer.core.organizer import (
    QUARANTINE_DIRNAME,
    apply_organization,
    build_duplicate_report,
    plan_organization,
    quarantine_duplicates,
)
from foto_organizer.core.scanner import MediaFile, scan_directory
from foto_organizer.core.verifier import verify_backup, write_verification_report
from foto_organizer.ui.duplicates_dialog import DuplicatesDialog
from foto_organizer.ui.gallery_view import GalleryView
from foto_organizer.ui.help_dialog import HelpDialog
from foto_organizer.ui.settings_dialog import SettingsDialog
from foto_organizer.ui.verification_dialog import VerificationDialog
from foto_organizer.ui.workers import OperationWorker, QtLogSink
from foto_organizer.utils.app_settings import AppSettings, load_settings, save_settings

THUMBNAIL_CACHE_DIR = Path.home() / ".foto_organizer" / "thumbnail_cache"


class MainWindow(QMainWindow):
    """Ventana principal: menú, árbol de carpetas, galería y panel de progreso."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Organizador de Fotos y Vídeos")
        self.resize(1100, 700)

        self._settings: AppSettings = load_settings()
        self._source_dir: Path | None = None
        self._backup_dir: Path | None = None
        self._media_files: list[MediaFile] = []
        self._worker: OperationWorker | None = None

        self._tree_model = QFileSystemModel(self)
        self._tree_view = QTreeView()
        self._tree_view.setModel(self._tree_model)
        for column in range(1, 4):
            self._tree_view.hideColumn(column)

        self._gallery = GalleryView()

        splitter = QSplitter()
        splitter.addWidget(self._tree_view)
        splitter.addWidget(self._gallery)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self._progress_bar)

        self._build_progress_dock()
        self._build_menus()
        self._attach_log_sink()

    # --- Menús (F-30) -------------------------------------------------------

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&Archivo")
        file_menu.addAction("Seleccionar origen…", self._choose_source_dir)
        file_menu.addAction("Seleccionar destino de backup…", self._choose_backup_dir)
        file_menu.addSeparator()
        file_menu.addAction("Salir", self.close)

        tools_menu = self.menuBar().addMenu("&Herramientas")
        tools_menu.addAction("Escanear origen", self._scan_source)
        tools_menu.addAction("Ejecutar backup", self._run_backup)
        tools_menu.addAction(
            "Verificar backup y borrar origen…", self._verify_and_delete
        )
        tools_menu.addAction("Buscar duplicados", self._find_duplicates)
        tools_menu.addAction("Organizar por fecha…", self._organize_by_date)
        tools_menu.addSeparator()
        tools_menu.addAction("Configuración…", self._open_settings)

        help_menu = self.menuBar().addMenu("A&yuda")
        help_menu.addAction("Guía de uso", self._show_help)
        help_menu.addAction("Acerca de", self._show_about)

    # --- Panel de progreso (F-33) -------------------------------------------

    def _build_progress_dock(self) -> None:
        dock = QDockWidget("Progreso", self)
        content = QWidget()
        layout = QVBoxLayout(content)

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        layout.addWidget(self._log_view)

        cancel_button = QPushButton("Cancelar operación")
        cancel_button.clicked.connect(self._cancel_operation)
        layout.addWidget(cancel_button)

        dock.setWidget(content)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

    def _attach_log_sink(self) -> None:
        self._log_sink = QtLogSink()
        self._log_sink.message_logged.connect(self._log_view.appendPlainText)
        logger.add(
            self._log_sink.write, level="INFO", format="{time:HH:mm:ss} | {message}"
        )

    def _cancel_operation(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            logger.warning("Cancelando operación en curso a petición del usuario")
            self._worker.terminate()
            self._worker.wait()
            self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        self._progress_bar.setVisible(busy)

    def _run_in_background(self, func: object) -> None:
        self._worker = OperationWorker(func)  # type: ignore[arg-type]
        self._worker.succeeded.connect(self._on_worker_succeeded)
        self._worker.failed.connect(self._on_worker_failed)
        self._set_busy(True)
        self._worker.start()

    def _on_worker_succeeded(self, result: object) -> None:
        self._set_busy(False)

    def _on_worker_failed(self, message: str) -> None:
        self._set_busy(False)
        QMessageBox.critical(self, "Error", message)

    # --- Selección de directorios (F-31) -------------------------------------

    def _choose_source_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio origen"
        )
        if not directory:
            return
        if self._backup_dir is not None and Path(directory) == self._backup_dir:
            QMessageBox.warning(
                self,
                "Directorios inválidos",
                "El origen no puede ser igual al destino.",
            )
            return
        self._source_dir = Path(directory)
        self._tree_model.setRootPath(directory)
        self._tree_view.setRootIndex(self._tree_model.index(directory))
        self.statusBar().showMessage(f"Origen: {directory}")

    def _choose_backup_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de backup"
        )
        if not directory:
            return
        if self._source_dir is not None and Path(directory) == self._source_dir:
            QMessageBox.warning(
                self,
                "Directorios inválidos",
                "El destino no puede ser igual al origen.",
            )
            return
        self._backup_dir = Path(directory)
        self.statusBar().showMessage(f"Backup: {directory}")

    # --- Acciones de Herramientas --------------------------------------------

    def _require_source_dir(self) -> Path | None:
        if self._source_dir is None:
            QMessageBox.warning(
                self, "Falta el origen", "Selecciona primero un directorio origen."
            )
            return None
        return self._source_dir

    def _scan_source(self) -> None:
        source = self._require_source_dir()
        if source is None:
            return
        self._scan_and_populate_gallery(source)
        self.statusBar().showMessage(f"{len(self._media_files)} archivo(s) encontrados")

    def _scan_and_populate_gallery(self, source: Path) -> None:
        """Escanea ``source`` y refresca la galería, para que cualquier acción que
        dispare un escaneo (no solo "Escanear origen") deje ver los thumbnails."""
        self._media_files = scan_directory(source)
        self._gallery.set_media_files(self._media_files, THUMBNAIL_CACHE_DIR)

    def _run_backup(self) -> None:
        source = self._require_source_dir()
        backup_dir = self._backup_dir
        if source is None or backup_dir is None:
            QMessageBox.warning(
                self, "Falta el destino", "Selecciona un directorio de backup."
            )
            return
        self._run_in_background(lambda: run_backup(source, backup_dir))

    def _verify_and_delete(self) -> None:
        backup_dir = self._backup_dir
        if backup_dir is None:
            QMessageBox.warning(self, "Falta el backup", "Ejecuta primero un backup.")
            return
        from foto_organizer.core.backup import load_manifest
        from foto_organizer.core.cleaner import delete_verified_sources

        manifest = load_manifest(backup_dir)
        results = verify_backup(manifest)
        write_verification_report(results, backup_dir)

        dialog = VerificationDialog(results, self)
        if dialog.exec() != VerificationDialog.DialogCode.Accepted:
            return

        try:
            delete_verified_sources(
                results,
                confirmation_phrase=dialog.confirmation_phrase(),
                audit_log_path=backup_dir / "audit_log.jsonl",
            )
        except Exception as exc:  # noqa: BLE001 - se muestra al usuario
            QMessageBox.critical(self, "Borrado no autorizado", str(exc))
            return
        QMessageBox.information(
            self, "Borrado completado", "Archivos origen borrados tras verificación."
        )

    def _find_duplicates(self) -> None:
        source = self._require_source_dir()
        if source is None:
            return
        if not self._media_files:
            self._scan_and_populate_gallery(source)

        report = build_duplicate_report(self._media_files)
        dialog = DuplicatesDialog(report, self)
        if dialog.exec() != DuplicatesDialog.DialogCode.Accepted:
            return

        to_remove = dialog.paths_to_remove()
        if not to_remove:
            return
        quarantine_duplicates(to_remove, source)
        message = (
            f"{len(to_remove)} duplicado(s) movido(s) a "
            f"'{QUARANTINE_DIRNAME}' dentro del origen para tu revisión."
        )
        backup_exists = (
            self._backup_dir is not None
            and (self._backup_dir / MANIFEST_FILENAME).is_file()
        )
        if backup_exists:
            message += (
                "\n\nYa existe un backup para este origen: sus rutas quedaron "
                "desactualizadas por este movimiento. Vuelve a ejecutar "
                '"Ejecutar backup" antes de verificar y borrar el origen, o la '
                "verificación marcará estos archivos como 'faltantes' y bloqueará "
                "el borrado de todo el backup."
            )
        QMessageBox.information(self, "Duplicados movidos", message)
        self._scan_and_populate_gallery(source)

    def _organize_by_date(self) -> None:
        if not self._media_files:
            source = self._require_source_dir()
            if source is None:
                return
            self._scan_and_populate_gallery(source)

        destination = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio destino organizado"
        )
        if not destination:
            return

        entries = plan_organization(self._media_files, Path(destination))
        self._run_in_background(lambda: apply_organization(entries))

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._settings = dialog.settings()
            save_settings(self._settings)

    def _show_help(self) -> None:
        HelpDialog(self).exec()

    def _show_about(self) -> None:
        QMessageBox.information(
            self,
            "Acerca de",
            "Organizador de Fotos y Vídeos\n"
            "Backup seguro, organización y verificación de integridad.",
        )
