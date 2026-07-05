"""Tests del worker en segundo plano y del sink de log Qt (F-33).

``run()`` se invoca de forma síncrona: coverage no traza hilos nativos de
``QThread``, y la entrega de señales entre hilos ya la cubren los tests de
``MainWindow`` (``test_run_in_background_*``).
"""

from pytestqt.qtbot import QtBot

from foto_organizer.ui.workers import OperationWorker, QtLogSink


def test_operation_worker_emits_succeeded_with_result(qtbot: QtBot) -> None:
    worker = OperationWorker(lambda: 42)
    results: list[object] = []
    worker.succeeded.connect(results.append)

    worker.run()

    assert results == [42]


def test_operation_worker_emits_failed_on_exception(qtbot: QtBot) -> None:
    def _boom() -> None:
        raise ValueError("fallo simulado")

    worker = OperationWorker(_boom)
    errors: list[str] = []
    failures: list[object] = []
    worker.failed.connect(errors.append)
    worker.succeeded.connect(failures.append)

    worker.run()

    assert errors == ["fallo simulado"]
    assert failures == []


def test_qt_log_sink_forwards_message_without_trailing_newline(qtbot: QtBot) -> None:
    sink = QtLogSink()
    received: list[str] = []
    sink.message_logged.connect(received.append)

    sink.write("hola mundo\n")

    assert received == ["hola mundo"]
