"""Tests Fase 4 — RAG (loaders, chunker, indexer incremental, citas)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.providers.base import ChatMessage, LLMResponse
from jarvis.rag.base import Citation, DocumentChunk, RAGAnswer, RetrievedChunk
from jarvis.rag.chunker import SlidingWindowChunker
from jarvis.rag.indexer import IncrementalIndexer
from jarvis.rag.loaders import CompositeLoader, TextLoader
from jarvis.rag.orchestrator import RAGOrchestrator
from jarvis.skills.builtin.ask_docs import AskDocsSkill


class FakeEmbed:
    name = "fake"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        import hashlib

        # bag-of-words estable (hash() de Python no lo es entre procesos)
        vec = [0.0] * 32
        for token in text.lower().split():
            digest = hashlib.md5(token.encode()).hexdigest()
            vec[int(digest[:8], 16) % 32] += 1.0
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / norm for x in vec]


class FakeStore:
    name = "fake_store"

    def __init__(self) -> None:
        self.items: list[tuple[DocumentChunk, list[float]]] = []

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        for c, e in zip(chunks, embeddings, strict=True):
            self.items.append((c, e))

    def delete_by_source(self, source: str) -> None:
        self.items = [(c, e) for c, e in self.items if c.source != source]

    def query(self, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        scored: list[RetrievedChunk] = []
        for chunk, emb in self.items:
            # cosine
            dot = sum(a * b for a, b in zip(embedding, emb, strict=False))
            scored.append(RetrievedChunk(chunk=chunk, score=float(dot)))
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]


class FakeLLM:
    name = "fake_llm"

    def chat(self, messages: list[ChatMessage]) -> LLMResponse:
        return LLMResponse(
            text="Respuesta basada en contexto [1].",
            model="fake",
            provider="fake",
        )


def test_text_loader(tmp_path: Path) -> None:
    f = tmp_path / "nota.md"
    f.write_text("# Hola\nVacaciones: 15 días.", encoding="utf-8")
    docs = TextLoader().load(f)
    assert len(docs) == 1
    assert "Vacaciones" in docs[0].text


def test_chunker_overlap() -> None:
    from jarvis.rag.base import RawDocument

    docs = [RawDocument(source="x", text="palabra " * 200)]
    chunks = SlidingWindowChunker(chunk_size=80, overlap=20).chunk(docs)
    assert len(chunks) >= 2
    assert all(c.source == "x" for c in chunks)


def test_incremental_skips_unchanged(tmp_path: Path) -> None:
    doc = tmp_path / "manual.md"
    doc.write_text(
        "Los empleados tienen 15 días hábiles de vacaciones. "
        "Kubernetes despliega jarvis-api.",
        encoding="utf-8",
    )
    store = FakeStore()
    indexer = IncrementalIndexer(
        loader=CompositeLoader(),
        chunker=SlidingWindowChunker(chunk_size=200, overlap=20),
        embeddings=FakeEmbed(),
        store=store,
        index_db=tmp_path / "rag.db",
        workers=2,
    )
    s1 = indexer.index_path(tmp_path)
    assert s1["indexed"] == 1
    assert s1["chunks"] >= 1
    n_after = len(store.items)
    s2 = indexer.index_path(tmp_path)
    assert s2["indexed"] == 0
    assert s2["skipped_unchanged"] == 1
    assert len(store.items) == n_after

    doc.write_text(doc.read_text(encoding="utf-8") + "\nNueva cláusula de impuestos.", encoding="utf-8")
    s3 = indexer.index_path(tmp_path)
    assert s3["indexed"] == 1


def test_orchestrator_cites_and_refuses() -> None:
    store = FakeStore()
    emb = FakeEmbed()
    chunk = DocumentChunk(
        id="1",
        text="Vacaciones: 15 días hábiles al año con 10 días de anticipación.",
        source="/docs/contrato.md",
        page=2,
    )
    store.upsert([chunk], emb.embed_documents([chunk.text]))

    class FakeRetriever:
        name = "fake_retriever"

        def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
            return store.query(emb.embed_query(query), top_k)

    orch = RAGOrchestrator(
        FakeRetriever(),
        FakeLLM(),
        top_k=3,
        min_score=0.01,
        refuse_if_insufficient=True,
    )
    ans = orch.ask("¿Qué dice el contrato sobre vacaciones?")
    assert ans.sufficient
    assert ans.citations
    assert "Fuentes" in ans.answer
    assert ans.citations[0].page == 2

    ans2 = orch.ask("¿Qué dice el contrato sobre vacaciones?")
    assert ans2.used_session_cache is True

    class EmptyRetriever:
        name = "empty"

        def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
            return []

    orch2 = RAGOrchestrator(EmptyRetriever(), FakeLLM(), min_score=0.9)
    bad = orch2.ask("algo que no existe xyzzy")
    assert bad.sufficient is False
    assert "evidencia" in bad.answer.lower()


def test_ask_docs_skill_score() -> None:
    skill = AskDocsSkill()
    assert skill.can_handle("¿Qué dice el manual sobre la instalación?") >= 0.8
    assert skill.can_handle("hola qué tal") < 0.5
