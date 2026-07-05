"""Tests del punto de entrada ``python -m foto_organizer``."""

from pathlib import Path

import pytest

import foto_organizer.__main__ as entry_point


def test_main_configures_logging_shows_window_and_exits_with_app_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class FakeApp:
        def __init__(self, argv: list[str]) -> None:
            events.append("app-creada")

        def exec(self) -> int:
            events.append("app-exec")
            return 7

    class FakeWindow:
        def show(self) -> None:
            events.append("window-show")

    def fake_setup_logging(
        log_dir: Path | None = None, console_level: str = "INFO"
    ) -> None:
        events.append("logging")

    monkeypatch.setattr(entry_point, "setup_logging", fake_setup_logging)
    monkeypatch.setattr(entry_point, "QApplication", FakeApp)
    monkeypatch.setattr(entry_point, "MainWindow", FakeWindow)

    with pytest.raises(SystemExit) as excinfo:
        entry_point.main()

    assert excinfo.value.code == 7
    assert events == ["logging", "app-creada", "window-show", "app-exec"]
