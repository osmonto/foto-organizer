"""Tests de la vista de duplicados (F-35)."""

from datetime import UTC, datetime
from pathlib import Path

from pytestqt.qtbot import QtBot

from foto_organizer.core.organizer import DuplicateGroup, DuplicateReport
from foto_organizer.ui.duplicates_dialog import DuplicatesDialog


def _report(*groups: DuplicateGroup) -> DuplicateReport:
    return DuplicateReport(
        generated_at=datetime.now(UTC).isoformat(),
        confirmed_by_hash=list(groups),
        heuristic_by_name_and_size=[],
    )


def test_defaults_to_keeping_first_path_of_each_group(qtbot: QtBot) -> None:
    report = _report(
        DuplicateGroup(key="hash1", paths=["/a/1.jpg", "/a/2.jpg", "/a/3.jpg"])
    )
    dialog = DuplicatesDialog(report)
    qtbot.addWidget(dialog)

    assert dialog.paths_to_remove() == ["/a/2.jpg", "/a/3.jpg"]


def test_selecting_a_different_radio_changes_paths_to_remove(qtbot: QtBot) -> None:
    report = _report(DuplicateGroup(key="hash1", paths=["/a/1.jpg", "/a/2.jpg"]))
    dialog = DuplicatesDialog(report)
    qtbot.addWidget(dialog)

    button_group = dialog._button_groups[0]
    button_group.buttons()[1].setChecked(True)

    assert dialog.paths_to_remove() == ["/a/1.jpg"]


def test_empty_report_shows_no_groups(qtbot: QtBot) -> None:
    dialog = DuplicatesDialog(_report())
    qtbot.addWidget(dialog)

    assert dialog.paths_to_remove() == []


def test_each_option_shows_a_thumbnail_next_to_its_radio_button(
    qtbot: QtBot, tmp_path: Path
) -> None:
    from PIL import Image
    from PySide6.QtWidgets import QGroupBox, QLabel

    photo_a = tmp_path / "foto1.jpg"
    photo_b = tmp_path / "foto2.jpg"
    Image.new("RGB", (50, 50), color="green").save(photo_a)
    Image.new("RGB", (50, 50), color="green").save(photo_b)

    report = _report(DuplicateGroup(key="hash1", paths=[str(photo_a), str(photo_b)]))
    dialog = DuplicatesDialog(report)
    qtbot.addWidget(dialog)

    box = dialog.findChildren(QGroupBox)[0]
    thumbnails_with_pixmap = [
        label for label in box.findChildren(QLabel) if not label.pixmap().isNull()
    ]
    assert len(thumbnails_with_pixmap) == 2
