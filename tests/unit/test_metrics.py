"""Tests de métricas."""

from jarvis.events import EventBus
from jarvis.utils.metrics import MetricsCollector


def test_measure_records_ms() -> None:
    bus = EventBus()
    m = MetricsCollector(bus, enabled=True, log_system=False)
    m.begin_turn()
    with m.measure("stt_ms"):
        pass
    turn = m.end_turn()
    assert turn.stt_ms is not None
    assert turn.stt_ms >= 0
    assert turn.total_ms is not None
