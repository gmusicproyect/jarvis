"""Sistema centralizado de errores y recuperación."""

from __future__ import annotations

import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.hardening")


@dataclass
class FailureRecord:
    module: str
    error: str
    user_message: str
    recovered: bool = False
    recovery_action: str = ""
    traceback: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class ErrorHandler:
    """Captura fallos, registra y aplica recuperaciones registradas."""

    def __init__(self) -> None:
        self._recoveries: dict[str, Callable[[Exception], FailureRecord]] = {}
        self._history: list[FailureRecord] = []

    def register_recovery(
        self, module: str, fn: Callable[[Exception], FailureRecord]
    ) -> None:
        self._recoveries[module] = fn

    def handle(
        self,
        module: str,
        exc: BaseException,
        *,
        user_message: str | None = None,
    ) -> FailureRecord:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        msg = user_message or self._friendly(module, exc)
        record = FailureRecord(
            module=module,
            error=str(exc),
            user_message=msg,
            traceback=tb,
        )
        recovery = self._recoveries.get(module)
        if recovery is not None:
            try:
                recovered = recovery(exc if isinstance(exc, Exception) else Exception(str(exc)))
                record.recovered = recovered.recovered
                record.recovery_action = recovered.recovery_action
                if recovered.user_message:
                    record.user_message = recovered.user_message
            except Exception as rec_exc:  # noqa: BLE001
                _LOG.exception("recovery_failed", module=module, error=str(rec_exc))
        self._history.append(record)
        _LOG.error(
            "module_failure",
            module=module,
            error=record.error,
            recovered=record.recovered,
            recovery=record.recovery_action,
            user_message=record.user_message,
        )
        return record

    def recent(self, n: int = 20) -> list[FailureRecord]:
        return self._history[-n:]

    def _friendly(self, module: str, exc: BaseException) -> str:
        text = str(exc).lower()
        if module == "tts":
            return "No pude hablar con la voz principal; usaré una alternativa."
        if module == "ollama" or "connection" in text or "11434" in text:
            return (
                "Ollama no responde. Los comandos locales siguen disponibles; "
                "intentaré reconectar."
            )
        if module == "stt":
            return "Hubo un problema al reconocer la voz. Inténtalo de nuevo."
        return f"Algo falló en {module}. El detalle está en los logs."


# Singleton de proceso
_HANDLER: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    global _HANDLER
    if _HANDLER is None:
        _HANDLER = ErrorHandler()
    return _HANDLER
