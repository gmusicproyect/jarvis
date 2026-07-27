"""Factory de memoria según config."""

from __future__ import annotations

from pathlib import Path

from jarvis.config.loader import JarvisConfig, project_root
from jarvis.memory.semantic import ChromaSemanticMemory
from jarvis.memory.service import MemoryService
from jarvis.memory.session import WindowSessionMemory
from jarvis.memory.sqlite_store import SQLitePersistentMemory
from jarvis.utils.logging import get_logger


def build_memory_service(cfg: JarvisConfig) -> MemoryService | None:
    if not cfg.memory.enabled:
        return None

    root = project_root()
    log = get_logger("jarvis.memory.factory")

    db_path = Path(cfg.memory.db_path)
    if not db_path.is_absolute():
        db_path = root / db_path

    if cfg.memory.persistent_provider != "sqlite":
        raise ValueError(
            f"persistent_provider no soportado: {cfg.memory.persistent_provider}"
        )
    persistent = SQLitePersistentMemory(db_path)

    session = WindowSessionMemory(max_turns=cfg.memory.short_term_turns)

    semantic = None
    if cfg.memory.semantic_enabled and cfg.memory.semantic_provider == "chroma":
        chroma_dir = Path(cfg.memory.chroma_dir)
        if not chroma_dir.is_absolute():
            chroma_dir = root / chroma_dir
        semantic = ChromaSemanticMemory(
            chroma_dir,
            embedding_model=cfg.memory.embedding_model,
            embedding_base_url=cfg.memory.embedding_base_url
            or cfg.llm.base_url,
        )
    elif cfg.memory.semantic_enabled:
        log.warning(
            "semantic_provider_unsupported",
            provider=cfg.memory.semantic_provider,
        )

    return MemoryService(
        session=session,
        persistent=persistent,
        semantic=semantic,
        top_k=cfg.memory.top_k,
        user_name=cfg.app.user_name,
    )
