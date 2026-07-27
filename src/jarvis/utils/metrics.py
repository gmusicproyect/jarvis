"""Métricas de rendimiento del pipeline de voz."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

from jarvis.events.bus import METRICS_RECORDED, EventBus
from jarvis.utils.logging import get_logger

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]


@dataclass
class TurnMetrics:
    """Latencias de un ciclo wake → respuesta."""

    wake_detect_ms: float | None = None
    stt_ms: float | None = None
    llm_ms: float | None = None
    tts_ms: float | None = None
    total_ms: float | None = None
    cpu_percent: float | None = None
    ram_mb: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data = {
            "wake_detect_ms": self.wake_detect_ms,
            "stt_ms": self.stt_ms,
            "llm_ms": self.llm_ms,
            "tts_ms": self.tts_ms,
            "total_ms": self.total_ms,
            "cpu_percent": self.cpu_percent,
            "ram_mb": self.ram_mb,
        }
        data.update(self.extra)
        return {k: v for k, v in data.items() if v is not None}


class MetricsCollector:
    def __init__(self, bus: EventBus, *, enabled: bool = True, log_system: bool = True) -> None:
        self.bus = bus
        self.enabled = enabled
        self.log_system = log_system
        self._log = None
        self._turn = TurnMetrics()
        self._t0 = 0.0

    def _logger(self) -> Any:
        if self._log is None:
            self._log = get_logger("jarvis.metrics")
        return self._log

    def begin_turn(self) -> None:
        self._turn = TurnMetrics()
        self._t0 = time.perf_counter()
        if self.log_system and psutil is not None:
            proc = psutil.Process()
            self._turn.cpu_percent = proc.cpu_percent(interval=None)
            self._turn.ram_mb = proc.memory_info().rss / (1024 * 1024)

    def end_turn(self) -> TurnMetrics:
        if self._t0:
            self._turn.total_ms = (time.perf_counter() - self._t0) * 1000
        if self.enabled:
            payload = self._turn.as_dict()
            try:
                self._logger().info("turn_metrics", **payload)
            except Exception:  # noqa: BLE001
                pass
            self.bus.publish(METRICS_RECORDED, **payload)
        return self._turn

    def record(self, field_name: str, value_ms: float) -> None:
        setattr(self._turn, field_name, value_ms)

    @contextmanager
    def measure(self, field_name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.record(field_name, elapsed_ms)
