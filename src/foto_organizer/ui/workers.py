"""Ejecución de operaciones core en un hilo aparte, con log en vivo (F-33)."""

from collections.abc import Callable
from typing import Any

from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal


class OperationWorker(QThread):
    """Ejecuta ``func`` en un hilo aparte para no bloquear la interfaz.

    Cancelar una operación en curso (botón "Cancelar") termina el hilo a la
    fuerza: es seguro porque las operaciones de escritura solo tocan el
    destino (backup/organización), nunca el origen, así que como mucho deja
    una copia incompleta en destino.
    """

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, func: Callable[[], Any], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._func = func

    def run(self) -> None:
        try:
            result = self._func()
        except Exception as exc:  # noqa: BLE001 - se reporta a la UI, no se traga
            logger.exception("Operación fallida en segundo plano")
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(result)


class QtLogSink(QObject):
    """Sink de loguru que reenvía cada línea como señal Qt, para un log en vivo."""

    message_logged = Signal(str)

    def write(self, message: str) -> None:
        self.message_logged.emit(message.rstrip("\n"))
