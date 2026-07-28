"""Memoria persistente SQLite."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jarvis.memory.base import MemoryItem, MemoryKind
from jarvis.utils.logging import get_logger
import threading


class SQLitePersistentMemory:
    name = "sqlite"

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._log = get_logger("jarvis.memory.sqlite")
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA busy_timeout=5000;")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self._log.info("sqlite_ready", path=str(self._path))

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS profile (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memory_items (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memory_kind ON memory_items(kind);
            """
        )
        self._conn.commit()

    def upsert_profile(self, key: str, value: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO profile(key, value, updated_at) VALUES(?,?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (key, value, now),
        )
        self._conn.commit()

    def get_profile(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM profile WHERE key=?", (key,)
        ).fetchone()
        return None if row is None else str(row["value"])

    def all_profile(self) -> dict[str, str]:
        rows = self._conn.execute("SELECT key, value FROM profile").fetchall()
        return {str(r["key"]): str(r["value"]) for r in rows}

    def add_item(
        self, kind: MemoryKind, content: str, title: str | None = None
    ) -> MemoryItem:
        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        self._conn.execute(
            "INSERT INTO memory_items(id, kind, title, content, created_at) VALUES(?,?,?,?,?)",
            (item_id, kind.value, title, content, now.isoformat()),
        )
        self._conn.commit()
        return MemoryItem(
            id=item_id, kind=kind, content=content, title=title, created_at=now
        )

    def list_items(self, kind: MemoryKind | None = None) -> list[MemoryItem]:
        if kind is None:
            rows = self._conn.execute(
                "SELECT * FROM memory_items ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM memory_items WHERE kind=? ORDER BY created_at DESC",
                (kind.value,),
            ).fetchall()
        return [self._row_to_item(r) for r in rows]

    def search_items(
        self, query: str, kind: MemoryKind | None = None
    ) -> list[MemoryItem]:
        with self._lock:
                like = f"%{query.strip()}%"
                if kind is None:
                    rows = self._conn.execute(
                        """
                        SELECT * FROM memory_items
                        WHERE content LIKE ? OR IFNULL(title,'') LIKE ?
                        ORDER BY created_at DESC
                        """,
                        (like, like),
                    ).fetchall()
                else:
                    rows = self._conn.execute(
                        """
                        SELECT * FROM memory_items
                        WHERE kind=? AND (content LIKE ? OR IFNULL(title,'') LIKE ?)
                        ORDER BY created_at DESC
                        """,
                        (kind.value, like, like),
                    ).fetchall()
                return [self._row_to_item(r) for r in rows]

    def delete_item(self, item_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM memory_items WHERE id=?", (item_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def forget_matching(self, query: str) -> int:
        with self._lock:
                like = f"%{query.strip()}%"
                cur = self._conn.execute(
                    """
                    DELETE FROM memory_items
                    WHERE content LIKE ? OR IFNULL(title,'') LIKE ?
                    """,
                    (like, like),
                )
                # También limpia perfil si la clave/valor coincide
                self._conn.execute(
                    "DELETE FROM profile WHERE key LIKE ? OR value LIKE ?", (like, like)
                )
                self._conn.commit()
                return int(cur.rowcount)

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            id=str(row["id"]),
            kind=MemoryKind(str(row["kind"])),
            content=str(row["content"]),
            title=row["title"],
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
