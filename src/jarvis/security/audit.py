"""Auditoría unificada de seguridad / acciones."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from jarvis.utils.logging import get_logger
import threading


class SecurityAudit:
    def __init__(self, db_path: Path) -> None:
        self._log = get_logger("jarvis.security.audit")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA busy_timeout=5000;")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS security_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                user_name TEXT,
                action TEXT NOT NULL,
                skill TEXT,
                permission TEXT,
                result TEXT,
                detail TEXT
            )
            """
        )
        self._conn.commit()

    def record(
        self,
        *,
        user_name: str,
        action: str,
        skill: str | None = None,
        permission: str | None = None,
        result: str = "ok",
        detail: dict | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO security_audit(
                ts, user_name, action, skill, permission, result, detail
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                time.time(),
                user_name,
                action,
                skill,
                permission,
                result,
                json.dumps(detail or {}, ensure_ascii=False),
            ),
        )
        self._conn.commit()
        self._log.info(
            "security_audit",
            user=user_name,
            action=action,
            skill=skill,
            permission=permission,
            result=result,
        )
