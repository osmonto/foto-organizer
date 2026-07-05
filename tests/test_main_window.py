"""Tests de la ventana principal (F-30/F-31): construcción y validación de dirs."""

from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from foto_organizer.ui.main_window import MainWindow


def test_main_window_builds_without_error(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "Organizador de Fotos y Vídeos"
    assert len(window.menuBar().actions()) == 3


def test_scan_source_populates_gallery(qtbot: QtBot, tmp_path: Path) -> None:
    from datetime import datetime

    from PIL import Image

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (100, 100), color="green").save(source / "foto.jpg")

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    window._scan_source()

    assert len(window._media_files) == 1
    assert window._gallery.item_count() == 1
    assert isinstance(window._media_files[0].modified_at, datetime)


def test_find_duplicates_populates_gallery_even_without_prior_scan(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image

    from foto_organizer.ui.duplicates_dialog import DuplicatesDialog

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (100, 100), color="green").save(source / "foto.jpg")

    monkeypatch.setattr(DuplicatesDialog, "exec", lambda self: None)

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    # Regresión: ir directo a "Buscar duplicados" sin pasar antes por
    # "Escanear origen" debía dejar la galería vacía (F-32 solo se refrescaba
    # desde _scan_source), aunque _media_files sí se poblara.
    window._find_duplicates()

    assert len(window._media_files) == 1
    assert window._gallery.item_count() == 1


def test_find_duplicates_accepted_quarantines_unselected_duplicates(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image
    from PySide6.QtWidgets import QMessageBox

    from foto_organizer.core.organizer import QUARANTINE_DIRNAME
    from foto_organizer.ui.duplicates_dialog import DuplicatesDialog

    source = tmp_path / "source"
    source.mkdir()
    kept = source / "foto1.jpg"
    duplicate = source / "foto2.jpg"
    Image.new("RGB", (100, 100), color="green").save(kept)
    Image.new("RGB", (100, 100), color="green").save(duplicate)

    monkeypatch.setattr(
        DuplicatesDialog, "exec", lambda self: DuplicatesDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(
        DuplicatesDialog, "paths_to_remove", lambda self: [str(duplicate)]
    )
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    window._find_duplicates()

    assert not duplicate.exists()
    assert (source / QUARANTINE_DIRNAME / "foto2.jpg").is_file()
    assert kept.is_file()


def test_find_duplicates_warns_about_stale_backup_after_quarantine(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image
    from PySide6.QtWidgets import QMessageBox

    from foto_organizer.core.backup import MANIFEST_FILENAME
    from foto_organizer.ui.duplicates_dialog import DuplicatesDialog

    source = tmp_path / "source"
    source.mkdir()
    duplicate = source / "foto2.jpg"
    Image.new("RGB", (100, 100), color="green").save(source / "foto1.jpg")
    Image.new("RGB", (100, 100), color="green").save(duplicate)

    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / MANIFEST_FILENAME).write_text("[]", encoding="utf-8")

    monkeypatch.setattr(
        DuplicatesDialog, "exec", lambda self: DuplicatesDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(
        DuplicatesDialog, "paths_to_remove", lambda self: [str(duplicate)]
    )
    shown_messages: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        staticmethod(lambda *a, **k: shown_messages.append(a[2])),
    )

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source
    window._backup_dir = backup_dir

    # Regresión: si ya existe un backup para este origen, mover un duplicado
    # a cuarentena desactualiza el manifiesto (verify_backup marcaría ese
    # archivo como MISSING y bloquearía el borrado de todo el backup). La app
    # debe avisar explícitamente en vez de dejar que el usuario lo descubra
    # a mitad del flujo de verificar-y-borrar.
    window._find_duplicates()

    assert len(shown_messages) == 1
    assert "backup" in shown_messages[0].lower()
    assert "Ejecutar backup" in shown_messages[0]


def test_choose_source_dir_rejects_same_as_backup_dir(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    window = MainWindow()
    qtbot.addWidget(window)
    window._backup_dir = tmp_path

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *a, **k: str(tmp_path)),
    )
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: None))

    window._choose_source_dir()

    assert window._source_dir is None


def test_choose_source_dir_sets_source_and_tree_root(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog

    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *a, **k: str(tmp_path)),
    )

    window._choose_source_dir()

    assert window._source_dir == tmp_path
    assert window._tree_model.rootPath() == str(tmp_path).replace("\\", "/")


def test_choose_source_dir_cancelled_keeps_source_unset(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog

    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: "")
    )

    window._choose_source_dir()

    assert window._source_dir is None


def test_choose_backup_dir_sets_backup(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog

    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *a, **k: str(tmp_path)),
    )

    window._choose_backup_dir()

    assert window._backup_dir == tmp_path


def test_choose_backup_dir_cancelled_keeps_backup_unset(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog

    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: "")
    )

    window._choose_backup_dir()

    assert window._backup_dir is None


def test_choose_backup_dir_rejects_same_as_source_dir(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = tmp_path
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *a, **k: str(tmp_path)),
    )
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: None))

    window._choose_backup_dir()

    assert window._backup_dir is None


def test_scan_source_without_source_dir_warns(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    warnings: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[1]))
    )
    window = MainWindow()
    qtbot.addWidget(window)

    window._scan_source()

    assert warnings == ["Falta el origen"]
    assert window._media_files == []


def test_cancel_operation_without_worker_is_noop(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    window._cancel_operation()  # no debe lanzar

    assert window._worker is None


def test_cancel_operation_terminates_running_worker(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from foto_organizer.ui.workers import OperationWorker

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    calls: list[str] = []
    monkeypatch.setattr(OperationWorker, "isRunning", lambda self: True)
    monkeypatch.setattr(
        OperationWorker, "terminate", lambda self: calls.append("terminate")
    )
    monkeypatch.setattr(OperationWorker, "wait", lambda self, *a: calls.append("wait"))
    window._worker = OperationWorker(lambda: None)
    window._progress_bar.setVisible(True)

    window._cancel_operation()

    assert calls == ["terminate", "wait"]
    assert not window._progress_bar.isVisible()


def test_run_in_background_success_hides_progress_bar(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window._run_in_background(lambda: "ok")

    assert window._progress_bar.isVisible()
    qtbot.waitUntil(lambda: not window._progress_bar.isVisible(), timeout=5000)


def test_run_in_background_failure_shows_error_dialog(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    errors: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", staticmethod(lambda *a, **k: errors.append(a[2]))
    )
    window = MainWindow()
    qtbot.addWidget(window)

    def _boom() -> None:
        raise ValueError("fallo simulado")

    window._run_in_background(_boom)

    qtbot.waitUntil(lambda: errors == ["fallo simulado"], timeout=5000)


def test_run_backup_without_backup_dir_warns(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    warnings: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[1]))
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = tmp_path

    window._run_backup()

    assert warnings == ["Falta el destino"]


def test_run_backup_writes_manifest_in_background(qtbot: QtBot, tmp_path: Path) -> None:
    from PIL import Image

    from foto_organizer.core.backup import MANIFEST_FILENAME

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (50, 50), color="green").save(source / "foto.jpg")
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()

    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source
    window._backup_dir = backup_dir

    window._run_backup()

    assert window._worker is not None
    qtbot.waitUntil(
        lambda: window._worker is not None and window._worker.isFinished(),
        timeout=5000,
    )
    assert (backup_dir / MANIFEST_FILENAME).is_file()
    assert (backup_dir / "foto.jpg").is_file()


def _backed_up_source(tmp_path: Path) -> tuple[Path, Path]:
    """Crea un origen con una foto y un backup ya ejecutado (manifest incluido)."""
    from PIL import Image

    from foto_organizer.core.backup import run_backup

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (50, 50), color="green").save(source / "foto.jpg")
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    run_backup(source, backup_dir)
    return source, backup_dir


def test_verify_and_delete_without_backup_dir_warns(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    warnings: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[1]))
    )
    window = MainWindow()
    qtbot.addWidget(window)

    window._verify_and_delete()

    assert warnings == ["Falta el backup"]


def test_verify_and_delete_rejected_dialog_keeps_sources(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from foto_organizer.ui.verification_dialog import VerificationDialog

    source, backup_dir = _backed_up_source(tmp_path)
    monkeypatch.setattr(
        VerificationDialog, "exec", lambda self: VerificationDialog.DialogCode.Rejected
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window._backup_dir = backup_dir

    window._verify_and_delete()

    assert (source / "foto.jpg").is_file()


def test_verify_and_delete_accepted_deletes_sources_and_writes_audit_log(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    from foto_organizer.core.cleaner import CONFIRMATION_PHRASE
    from foto_organizer.ui.verification_dialog import VerificationDialog

    source, backup_dir = _backed_up_source(tmp_path)
    monkeypatch.setattr(
        VerificationDialog, "exec", lambda self: VerificationDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(
        VerificationDialog, "confirmation_phrase", lambda self: CONFIRMATION_PHRASE
    )
    infos: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a[1]))
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window._backup_dir = backup_dir

    window._verify_and_delete()

    assert not (source / "foto.jpg").exists()
    assert (backup_dir / "foto.jpg").is_file()
    assert (backup_dir / "audit_log.jsonl").is_file()
    assert infos == ["Borrado completado"]


def test_verify_and_delete_wrong_phrase_shows_error_and_keeps_sources(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    from foto_organizer.ui.verification_dialog import VerificationDialog

    source, backup_dir = _backed_up_source(tmp_path)
    monkeypatch.setattr(
        VerificationDialog, "exec", lambda self: VerificationDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(
        VerificationDialog, "confirmation_phrase", lambda self: "frase incorrecta"
    )
    errors: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", staticmethod(lambda *a, **k: errors.append(a[1]))
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window._backup_dir = backup_dir

    window._verify_and_delete()

    assert (source / "foto.jpg").is_file()
    assert errors == ["Borrado no autorizado"]


def test_find_duplicates_without_source_dir_warns(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    warnings: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[1]))
    )
    window = MainWindow()
    qtbot.addWidget(window)

    window._find_duplicates()

    assert warnings == ["Falta el origen"]


def test_find_duplicates_accepted_without_selection_does_nothing(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image

    from foto_organizer.core.organizer import QUARANTINE_DIRNAME
    from foto_organizer.ui.duplicates_dialog import DuplicatesDialog

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (50, 50), color="green").save(source / "foto.jpg")
    monkeypatch.setattr(
        DuplicatesDialog, "exec", lambda self: DuplicatesDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(DuplicatesDialog, "paths_to_remove", lambda self: [])
    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    window._find_duplicates()

    assert not (source / QUARANTINE_DIRNAME).exists()
    assert (source / "foto.jpg").is_file()


def test_organize_by_date_without_source_dir_warns(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    warnings: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[1]))
    )
    window = MainWindow()
    qtbot.addWidget(window)

    window._organize_by_date()

    assert warnings == ["Falta el origen"]


def test_organize_by_date_cancelled_destination_starts_no_worker(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image
    from PySide6.QtWidgets import QFileDialog

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (50, 50), color="green").save(source / "foto.jpg")
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: "")
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    window._organize_by_date()

    assert len(window._media_files) == 1  # escaneó antes de pedir destino
    assert window._worker is None


def test_organize_by_date_copies_files_into_destination(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image
    from PySide6.QtWidgets import QFileDialog

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (50, 50), color="green").save(source / "foto.jpg")
    destination = tmp_path / "organizado"
    destination.mkdir()
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *a, **k: str(destination)),
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window._source_dir = source

    window._organize_by_date()

    assert window._worker is not None
    qtbot.waitUntil(
        lambda: window._worker is not None and window._worker.isFinished(),
        timeout=5000,
    )
    assert len(list(destination.rglob("*.jpg"))) == 1
    assert (source / "foto.jpg").is_file()  # organizar nunca toca el origen


def test_open_settings_accepted_saves_settings(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from foto_organizer.ui.settings_dialog import SettingsDialog

    monkeypatch.setattr(
        SettingsDialog, "exec", lambda self: SettingsDialog.DialogCode.Accepted
    )
    saved: list[object] = []
    monkeypatch.setattr("foto_organizer.ui.main_window.save_settings", saved.append)
    window = MainWindow()
    qtbot.addWidget(window)

    window._open_settings()

    assert len(saved) == 1
    assert window._settings == saved[0]


def test_show_help_opens_help_dialog(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from foto_organizer.ui.help_dialog import HelpDialog

    opened: list[bool] = []
    monkeypatch.setattr(HelpDialog, "exec", lambda self: opened.append(True))
    window = MainWindow()
    qtbot.addWidget(window)

    window._show_help()

    assert opened == [True]


def test_show_about_shows_app_description(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    infos: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a[2]))
    )
    window = MainWindow()
    qtbot.addWidget(window)

    window._show_about()

    assert len(infos) == 1
    assert "Organizador de Fotos" in infos[0]
