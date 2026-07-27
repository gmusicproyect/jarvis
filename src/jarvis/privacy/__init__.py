"""Privacidad: exportar datos, borrar memoria, modo privacidad."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import JarvisConfig, clear_config_cache, project_root
from jarvis.gui.api.config_store import save_config_updates
from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.privacy")


def export_personal_data(cfg: JarvisConfig, dest: Path | None = None) -> Path:
    """Exporta perfil, memoria, preferencias, refs RAG y snapshot de config."""
    root = project_root()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = dest or (root / "data" / "exports" / f"jarvis-export-{stamp}.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_name": cfg.app.user_name,
        "profile": {},
        "memory_items": [],
        "preferences": {},
        "config_snapshot": {
            "language": cfg.app.language,
            "performance_profile": getattr(cfg.app, "performance_profile", "balanced"),
            "privacy_mode": getattr(cfg.security, "privacy_mode", False),
            "llm_model": cfg.llm.model,
            "tts_voice": cfg.tts.voice,
            "knowledge_dir": cfg.rag.knowledge_dir,
            "onboarding_completed": getattr(cfg.app, "onboarding_completed", False),
        },
        "indexed_documents": [],  # referencias, no copia de archivos
        "plugins": [],
    }

    db_path = root / cfg.memory.db_path
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            for row in conn.execute("SELECT key, value, updated_at FROM profile"):
                key = str(row["key"])
                entry = {
                    "value": str(row["value"]),
                    "updated_at": str(row["updated_at"]),
                }
                payload["profile"][key] = entry
                if key not in {"name"}:
                    payload["preferences"][key] = entry
            for row in conn.execute(
                "SELECT id, kind, title, content, created_at FROM memory_items "
                "ORDER BY created_at DESC"
            ):
                payload["memory_items"].append(
                    {
                        "id": str(row["id"]),
                        "kind": str(row["kind"]),
                        "title": row["title"],
                        "content": str(row["content"]),
                        "created_at": str(row["created_at"]),
                    }
                )
        finally:
            conn.close()

    # Referencias a documentos indexados (RAG), sin duplicar binarios
    rag_db = root / cfg.rag.index_db
    if rag_db.exists():
        try:
            conn = sqlite3.connect(rag_db)
            conn.row_factory = sqlite3.Row
            # esquema flexible: intenta tablas comunes
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "files" in tables:
                for row in conn.execute(
                    "SELECT * FROM files LIMIT 500"
                ):
                    payload["indexed_documents"].append(
                        {k: row[k] for k in row.keys()}
                    )
            elif "documents" in tables:
                for row in conn.execute(
                    "SELECT * FROM documents LIMIT 500"
                ):
                    payload["indexed_documents"].append(
                        {k: row[k] for k in row.keys()}
                    )
            else:
                # fallback: listar knowledge/
                knowledge = root / cfg.rag.knowledge_dir
                if knowledge.exists():
                    for p in sorted(knowledge.rglob("*")):
                        if p.is_file():
                            payload["indexed_documents"].append(
                                {
                                    "path": str(p.relative_to(root)),
                                    "size": p.stat().st_size,
                                    "source": "knowledge_dir_listing",
                                }
                            )
            conn.close()
        except Exception as exc:  # noqa: BLE001
            payload["indexed_documents"].append({"error": str(exc)})
    else:
        knowledge = root / cfg.rag.knowledge_dir
        if knowledge.exists():
            for p in sorted(knowledge.rglob("*")):
                if p.is_file():
                    payload["indexed_documents"].append(
                        {
                            "path": str(p.relative_to(root)),
                            "size": p.stat().st_size,
                            "source": "knowledge_dir_listing",
                        }
                    )

    plugins_dir = root / "plugins"
    if plugins_dir.exists():
        for child in sorted(plugins_dir.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                manifest = child / "manifest.yaml"
                payload["plugins"].append(
                    {
                        "name": child.name,
                        "has_manifest": manifest.exists(),
                    }
                )

    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _LOG.info(
        "privacy_export",
        path=str(out),
        items=len(payload["memory_items"]),
        docs=len(payload["indexed_documents"]),
    )
    return out


def wipe_all_memory(cfg: JarvisConfig, *, keep_user_name: bool = False) -> dict[str, int]:
    """Borra memoria SQLite + índices Chroma de memoria. No toca knowledge/ RAG docs."""
    root = project_root()
    stats = {"sqlite_items": 0, "profile_keys": 0, "chroma_cleared": 0}

    db_path = root / cfg.memory.db_path
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute("SELECT COUNT(*) FROM memory_items").fetchone()
            stats["sqlite_items"] = int(row[0]) if row else 0
            conn.execute("DELETE FROM memory_items")
            if keep_user_name:
                # conserva solo name
                rows = conn.execute("SELECT key FROM profile").fetchall()
                for (key,) in rows:
                    if key != "name":
                        conn.execute("DELETE FROM profile WHERE key=?", (key,))
                        stats["profile_keys"] += 1
            else:
                row = conn.execute("SELECT COUNT(*) FROM profile").fetchone()
                stats["profile_keys"] = int(row[0]) if row else 0
                conn.execute("DELETE FROM profile")
            conn.commit()
        finally:
            conn.close()

    chroma_dir = root / cfg.memory.chroma_dir
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir, ignore_errors=True)
        stats["chroma_cleared"] = 1
        chroma_dir.mkdir(parents=True, exist_ok=True)

    clear_config_cache()
    _LOG.info("privacy_wipe", **stats)
    return stats


def set_privacy_mode(enabled: bool) -> None:
    """Activa/desactiva modo privacidad (menos retención de contexto)."""
    updates: dict[str, Any] = {
        "security.privacy_mode": bool(enabled),
    }
    if enabled:
        updates["memory.short_term_turns"] = 5
        updates["memory.semantic_enabled"] = False
        updates["logging.level"] = "WARNING"
    save_config_updates(updates)
    clear_config_cache()
    _LOG.info("privacy_mode", enabled=enabled)


def is_full_forget_command(text: str) -> bool:
    """Detecta «elimina todo lo que recuerdas de mí» y variantes."""
    t = text.lower().strip()
    needles = [
        "elimina todo lo que recuerdas de mí",
        "elimina todo lo que recuerdas de mi",
        "borra toda mi memoria",
        "borra todo lo que sabes de mí",
        "borra todo lo que sabes de mi",
        "olvida todo sobre mí",
        "olvida todo sobre mi",
        "elimina todos mis recuerdos",
        "borra todos mis datos",
    ]
    return any(n in t for n in needles)
