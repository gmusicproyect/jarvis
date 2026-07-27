"""Tests de memoria Fase 2."""

from __future__ import annotations

from pathlib import Path

from jarvis.memory.service import MemoryAction, MemoryService, parse_memory_command
from jarvis.memory.session import WindowSessionMemory
from jarvis.memory.sqlite_store import SQLitePersistentMemory


def test_parse_remember_name() -> None:
    cmd = parse_memory_command("Recuerda que mi nombre es Carlos")
    assert cmd.action == MemoryAction.REMEMBER_NAME
    assert "Carlos" in cmd.payload


def test_parse_note_and_forget() -> None:
    assert parse_memory_command("Guarda esta nota: comprar cuerdas").action == MemoryAction.SAVE_NOTE
    assert parse_memory_command("Muéstrame mis notas").action == MemoryAction.LIST_NOTES
    assert parse_memory_command("Olvida comprar cuerdas").action == MemoryAction.FORGET


def test_sqlite_persists(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    store = SQLitePersistentMemory(db)
    store.upsert_profile("name", "Ana")
    store.close()

    store2 = SQLitePersistentMemory(db)
    assert store2.get_profile("name") == "Ana"
    store2.close()


def test_memory_service_remember_and_list(tmp_path: Path) -> None:
    db = tmp_path / "m.db"
    svc = MemoryService(
        session=WindowSessionMemory(6),
        persistent=SQLitePersistentMemory(db),
        semantic=None,
        user_name="Juan",
    )
    r1 = svc.handle_command("Guarda esta nota: reunión a las 5")
    assert r1 is not None
    r2 = svc.handle_command("Muéstrame mis notas")
    assert r2 is not None
    assert "reunión" in r2.lower() or "reunion" in r2.lower() or "5" in r2


def test_session_window() -> None:
    s = WindowSessionMemory(max_turns=4)
    for i in range(6):
        s.add("user", f"m{i}")
    assert len(s.history()) == 4
