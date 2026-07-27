"""Historial de análisis visuales."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from jarvis.vision.base import VisionAnalysis
from jarvis.utils.logging import get_logger


class VisionHistory:
    def __init__(self, db_path: Path) -> None:
        self._log = get_logger("jarvis.vision.history")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vision_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                image_path TEXT NOT NULL,
                source TEXT,
                question TEXT,
                answer TEXT,
                ocr_text TEXT,
                ocr_confidence REAL,
                summary TEXT,
                tags_json TEXT,
                model TEXT,
                elapsed_ms REAL
            )
            """
        )
        self._conn.commit()

    def save(self, analysis: VisionAnalysis, *, question: str = "") -> int:
        ocr_text = analysis.ocr.text if analysis.ocr else ""
        ocr_conf = analysis.ocr.confidence if analysis.ocr else None
        summary = analysis.vision.summary if analysis.vision else analysis.answer
        model = analysis.vision.model if analysis.vision else ""
        cur = self._conn.execute(
            """
            INSERT INTO vision_history(
                ts, image_path, source, question, answer, ocr_text,
                ocr_confidence, summary, tags_json, model, elapsed_ms
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                time.time(),
                str(analysis.image_path),
                analysis.source,
                question,
                analysis.answer,
                ocr_text,
                ocr_conf,
                summary,
                json.dumps(analysis.tags, ensure_ascii=False),
                model,
                analysis.elapsed_ms,
            ),
        )
        self._conn.commit()
        row_id = int(cur.lastrowid or 0)
        analysis.history_id = row_id
        self._log.info(
            "vision_history_saved",
            id=row_id,
            tags=analysis.tags,
            model=model,
        )
        return row_id
