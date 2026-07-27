"""Contratos de memoria (sesión / persistente / semántica)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable


class MemoryKind(str, Enum):
    PREFERENCE = "preference"
    PROFILE = "profile"
    NOTE = "note"
    PROJECT = "project"
    REMINDER = "reminder"
    FACT = "fact"
    CONVERSATION = "conversation"


@dataclass
class MemoryItem:
    id: str
    kind: MemoryKind
    content: str
    title: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass
class ChatTurn:
    role: str
    content: str


@runtime_checkable
class SessionMemory(Protocol):
    """Memoria de sesión (RAM, ventana limitada)."""

    name: str

    def add(self, role: str, content: str) -> None: ...

    def history(self) -> list[ChatTurn]: ...

    def clear(self) -> None: ...

    def as_messages(self) -> list[dict[str, str]]: ...


@runtime_checkable
class PersistentMemory(Protocol):
    """Memoria permanente (SQLite u otro)."""

    name: str

    def upsert_profile(self, key: str, value: str) -> None: ...

    def get_profile(self, key: str) -> str | None: ...

    def all_profile(self) -> dict[str, str]: ...

    def add_item(self, kind: MemoryKind, content: str, title: str | None = None) -> MemoryItem: ...

    def list_items(self, kind: MemoryKind | None = None) -> list[MemoryItem]: ...

    def search_items(self, query: str, kind: MemoryKind | None = None) -> list[MemoryItem]: ...

    def delete_item(self, item_id: str) -> bool: ...

    def forget_matching(self, query: str) -> int: ...


@runtime_checkable
class SemanticMemory(Protocol):
    """Memoria semántica / embeddings (Chroma, etc.)."""

    name: str

    def index(self, item: MemoryItem) -> None: ...

    def delete(self, item_id: str) -> None: ...

    def retrieve(self, query: str, top_k: int = 5) -> list[MemoryItem]: ...
