"""Memoria semántica con Chroma + embeddings locales (Ollama)."""

from __future__ import annotations

from pathlib import Path

import httpx

from jarvis.memory.base import MemoryItem, MemoryKind
from jarvis.utils.logging import get_logger


class ChromaSemanticMemory:
    """Índice vectorial local. Si Chroma/embeddings fallan, opera en modo no-op seguro."""

    name = "chroma"

    def __init__(
        self,
        persist_dir: Path,
        *,
        embedding_model: str = "nomic-embed-text",
        embedding_base_url: str = "http://127.0.0.1:11434",
    ) -> None:
        self._log = get_logger("jarvis.memory.semantic")
        self._model = embedding_model
        self._base = embedding_base_url.rstrip("/")
        self._enabled = True
        self._collection = None
        try:
            import chromadb

            persist_dir.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(persist_dir))
            self._collection = client.get_or_create_collection(
                name="jarvis_memory",
                metadata={"hnsw:space": "cosine"},
            )
            self._log.info("chroma_ready", path=str(persist_dir))
        except Exception as exc:  # noqa: BLE001
            self._enabled = False
            self._log.warning("chroma_disabled", error=str(exc))

    def _embed(self, text: str) -> list[float] | None:
        try:
            with httpx.Client(base_url=self._base, timeout=60.0) as client:
                # API nueva
                resp = client.post(
                    "/api/embed",
                    json={"model": self._model, "input": text},
                )
                if resp.status_code == 404:
                    resp = client.post(
                        "/api/embeddings",
                        json={"model": self._model, "prompt": text},
                    )
                resp.raise_for_status()
                data = resp.json()
                if "embeddings" in data and data["embeddings"]:
                    return list(data["embeddings"][0])
                emb = data.get("embedding")
                return list(emb) if emb else None
        except Exception as exc:  # noqa: BLE001
            self._log.warning("embed_failed", error=str(exc))
            return None

    def index(self, item: MemoryItem) -> None:
        if not self._enabled or self._collection is None:
            return
        emb = self._embed(item.content)
        if emb is None:
            return
        self._collection.upsert(
            ids=[item.id],
            embeddings=[emb],
            documents=[item.content],
            metadatas=[
                {
                    "kind": item.kind.value,
                    "title": item.title or "",
                }
            ],
        )

    def delete(self, item_id: str) -> None:
        if not self._enabled or self._collection is None:
            return
        try:
            self._collection.delete(ids=[item_id])
        except Exception:  # noqa: BLE001
            pass

    def retrieve(self, query: str, top_k: int = 5) -> list[MemoryItem]:
        if not self._enabled or self._collection is None:
            return []
        emb = self._embed(query)
        if emb is None:
            return []
        result = self._collection.query(
            query_embeddings=[emb],
            n_results=max(1, top_k),
            include=["documents", "metadatas"],
        )
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        items: list[MemoryItem] = []
        for i, doc, meta in zip(ids, docs, metas, strict=False):
            kind_raw = (meta or {}).get("kind", MemoryKind.FACT.value)
            try:
                kind = MemoryKind(kind_raw)
            except ValueError:
                kind = MemoryKind.FACT
            items.append(
                MemoryItem(
                    id=str(i),
                    kind=kind,
                    content=str(doc),
                    title=(meta or {}).get("title") or None,
                )
            )
        return items
