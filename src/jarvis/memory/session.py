"""Memoria de sesión en RAM con ventana limitada."""

from __future__ import annotations

from collections import deque

from jarvis.memory.base import ChatTurn


class WindowSessionMemory:
    name = "window"

    def __init__(self, max_turns: int = 20) -> None:
        self._max = max(2, max_turns)
        self._turns: deque[ChatTurn] = deque(maxlen=self._max)

    def add(self, role: str, content: str) -> None:
        text = content.strip()
        if not text:
            return
        self._turns.append(ChatTurn(role=role, content=text))

    def history(self) -> list[ChatTurn]:
        return list(self._turns)

    def clear(self) -> None:
        self._turns.clear()

    def as_messages(self) -> list[dict[str, str]]:
        return [{"role": t.role, "content": t.content} for t in self._turns]
