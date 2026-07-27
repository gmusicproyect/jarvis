"""Router de intención — Fase 1: cancel vs chat."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from unicodedata import normalize

from jarvis.config.loader import SessionConfig
from jarvis.utils.logging import get_logger


class IntentKind(str, Enum):
    CANCEL = "cancel"
    CHAT = "chat"
    EMPTY = "empty"


@dataclass(frozen=True)
class Intent:
    kind: IntentKind
    text: str
    matched_phrase: str | None = None


def _normalize(text: str) -> str:
    folded = normalize("NFD", text.lower())
    return "".join(c for c in folded if c.isalnum() or c.isspace()).strip()


class IntentRouter:
    def __init__(self, session: SessionConfig) -> None:
        self._phrases = [_normalize(p) for p in session.cancel_phrases]
        self._log = get_logger("jarvis.intent")

    def route(self, text: str) -> Intent:
        cleaned = text.strip()
        if not cleaned:
            return Intent(kind=IntentKind.EMPTY, text=cleaned)

        norm = _normalize(cleaned)
        for phrase in self._phrases:
            if norm == phrase or norm.startswith(phrase + " ") or f" {phrase}" in f" {norm}":
                self._log.info("intent_cancel", phrase=phrase, text=cleaned)
                return Intent(kind=IntentKind.CANCEL, text=cleaned, matched_phrase=phrase)

        return Intent(kind=IntentKind.CHAT, text=cleaned)
