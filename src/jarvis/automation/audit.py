"""Auditoría de acciones de automatización."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from jarvis.automation.base import ActionRequest, ActionResult
from jarvis.utils.logging import get_logger


class AutomationAudit:
    """Registra quién, cuándo, qué y el resultado de cada acción."""

    def __init__(self, db_path: Path) -> None:
        self._log = get_logger("jarvis.automation.audit")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automation_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                user_name TEXT NOT NULL,
                action TEXT NOT NULL,
                description TEXT NOT NULL,
                level INTEGER NOT NULL,
                success INTEGER NOT NULL,
                confirmed INTEGER,
                cancelled INTEGER NOT NULL,
                elapsed_ms REAL,
                error TEXT,
                data_json TEXT
            )
            """
        )
        self._conn.commit()

    def record(self, request: ActionRequest, result: ActionResult) -> None:
        self._conn.execute(
            """
            INSERT INTO automation_audit(
                ts, user_name, action, description, level,
                success, confirmed, cancelled, elapsed_ms, error, data_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                time.time(),
                request.user_name,
                result.action,
                request.description,
                int(request.level.value),
                1 if result.success else 0,
                (
                    None
                    if result.confirmed is None
                    else (1 if result.confirmed else 0)
                ),
                1 if result.cancelled else 0,
                result.elapsed_ms,
                result.error,
                json.dumps(result.data, ensure_ascii=False),
            ),
        )
        self._conn.commit()
        self._log.info(
            "automation_audit",
            action=result.action,
            level=request.level.value,
            success=result.success,
            confirmed=result.confirmed,
            cancelled=result.cancelled,
            elapsed_ms=result.elapsed_ms,
            user=request.user_name,
            error=result.error,
        )
