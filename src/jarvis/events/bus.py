"""Bus de eventos interno — desacopla módulos (Fase 1+)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from jarvis.utils.logging import get_logger

EventHandler = Callable[..., None]

# Eventos canónicos (contratos)
WAKE_DETECTED = "wake_detected"
SPEECH_RECOGNIZED = "speech_recognized"
INTENT_ROUTED = "intent_routed"
LLM_RESPONSE_READY = "llm_response_ready"
TTS_STARTED = "tts_started"
TTS_FINISHED = "tts_finished"
TTS_CANCELLED = "tts_cancelled"
FOLLOWUP_STARTED = "followup_started"
FOLLOWUP_ENDED = "followup_ended"
METRICS_RECORDED = "metrics_recorded"
ERROR = "error"
STATE_CHANGED = "state_changed"


class EventBus:
    """Pub/sub simple y síncrono (suficiente para el loop de voz)."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._log = None

    def _logger(self) -> Any:
        if self._log is None:
            self._log = get_logger("jarvis.events")
        return self._log

    def subscribe(self, event: str, handler: EventHandler) -> None:
        self._handlers[event].append(handler)

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    def publish(self, event: str, **payload: Any) -> None:
        try:
            self._logger().debug("event", event=event, **_safe(payload))
        except Exception:  # noqa: BLE001
            pass
        for handler in list(self._handlers.get(event, [])):
            try:
                handler(**payload)
            except Exception as exc:  # noqa: BLE001 — no tumbar el bus
                try:
                    self._logger().exception(
                        "event_handler_failed",
                        event=event,
                        handler=getattr(handler, "__name__", str(handler)),
                        error=str(exc),
                    )
                except Exception:  # noqa: BLE001
                    pass


def _safe(payload: dict[str, Any]) -> dict[str, Any]:
    """Evita logs enormes (p.ej. arrays de audio)."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if hasattr(value, "shape"):
            out[key] = f"ndarray{getattr(value, 'shape', '')}"
        elif isinstance(value, (bytes, bytearray)):
            out[key] = f"bytes[{len(value)}]"
        else:
            out[key] = value
    return out
