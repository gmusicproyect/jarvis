"""Tests del router de intención y cancelación."""

from jarvis.brain.intent import IntentKind, IntentRouter
from jarvis.config.loader import SessionConfig


def test_cancel_phrases() -> None:
    router = IntentRouter(SessionConfig())
    for phrase in ("cancela", "detente", "para", "silencio", "STOP"):
        assert router.route(phrase).kind == IntentKind.CANCEL


def test_chat_intent() -> None:
    router = IntentRouter(SessionConfig())
    intent = router.route("Qué hora es")
    assert intent.kind == IntentKind.CHAT


def test_empty() -> None:
    router = IntentRouter(SessionConfig())
    assert router.route("   ").kind == IntentKind.EMPTY
