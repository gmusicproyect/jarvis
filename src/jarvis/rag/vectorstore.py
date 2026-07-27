"""Vector store Chroma para documentos RAG."""

from __future__ import annotations

from pathlib import Path

import chromadb

from jarvis.rag.base import DocumentChunk, RetrievedChunk
from jarvis.utils.logging import get_logger


class ChromaVectorStore:
    name = "chroma"

    def __init__(self, persist_dir: Path, collection: str = "jarvis_docs") -> None:
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._log = get_logger("jarvis.rag.store")
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._col = self._client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )
        self._log.info("rag_chroma_ready", path=str(persist_dir), collection=collection)

    def upsert(
        self, chunks: list[DocumentChunk], embeddings: list[list[float]]
    ) -> None:
        if not chunks:
            return
        self._col.upsert(
            ids=[c.id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "source": c.source,
                    "page": "" if c.page is None else str(c.page),
                    **{k: str(v) for k, v in c.metadata.items()},
                }
                for c in chunks
            ],
        )

    def delete_by_source(self, source: str) -> None:
        try:
            self._col.delete(where={"source": source})
        except Exception:  # noqa: BLE001
            # fallback: query ids
            try:
                got = self._col.get(where={"source": source})
                ids = got.get("ids") or []
                if ids:
                    self._col.delete(ids=ids)
            except Exception as exc:  # noqa: BLE001
                self._log.warning("delete_source_failed", source=source, error=str(exc))

    def query(self, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        count = self._col.count()
        if count == 0:
            return []
        n = min(top_k, count)
        result = self._col.query(
            query_embeddings=[embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        out: list[RetrievedChunk] = []
        for i, doc, meta, dist in zip(ids, docs, metas, dists, strict=False):
            meta = meta or {}
            page_raw = meta.get("page") or ""
            page = int(page_raw) if str(page_raw).isdigit() else None
            # Chroma cosine distance: menor = mejor → score = 1/(1+d)
            score = 1.0 / (1.0 + float(dist))
            chunk = DocumentChunk(
                id=str(i),
                text=str(doc),
                source=str(meta.get("source", "")),
                page=page,
                metadata={k: str(v) for k, v in meta.items()},
            )
            out.append(RetrievedChunk(chunk=chunk, score=score))
        return out
