"""Contrato de shell GUI sustituible (Qt hoy, web/Tauri mañana)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from jarvis.gui.api.models import ConversationTurn, StatusSnapshot


@runtime_checkable
class GuiShell(Protocol):
    """Cualquier frontend debe implementar este contrato mínimo."""

    def run(self) -> int:
        """Arranca el loop de UI. Devuelve código de salida."""
        ...

    def show_main(self) -> None: ...

    def show_settings(self) -> None: ...

    def notify(self, title: str, message: str, *, level: str = "info") -> None: ...

    def append_conversation(self, turn: ConversationTurn) -> None: ...

    def refresh_status(self, snapshot: StatusSnapshot) -> None: ...
