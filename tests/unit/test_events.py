"""Tests del event bus."""

from jarvis.events import WAKE_DETECTED, EventBus


def test_publish_subscribe() -> None:
    bus = EventBus()
    seen: list[float] = []

    def on_wake(*, score: float, **_: object) -> None:
        seen.append(score)

    bus.subscribe(WAKE_DETECTED, on_wake)
    bus.publish(WAKE_DETECTED, score=0.9, via="wake")
    assert seen == [0.9]
