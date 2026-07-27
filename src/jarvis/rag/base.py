"""Contratos RAG — DocumentLoader, Chunker, Embedding, VectorStore, Retriever."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class RawDocument:
    source: str
    text: str
    page: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    id: str
    text: str
    source: str
    page: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float  # similitud 0–1 (mayor = mejor)


@dataclass
class Citation:
    source: str
    page: int | None
    fragment: str
    score: float


@dataclass
class RAGAnswer:
    answer: str
    citations: list[Citation]
    sufficient: bool
    used_session_cache: bool = False


@runtime_checkable
class DocumentLoader(Protocol):
    name: str

    def can_load(self, path: Path) -> bool: ...

    def load(self, path: Path) -> list[RawDocument]: ...


@runtime_checkable
class Chunker(Protocol):
    name: str

    def chunk(self, docs: list[RawDocument]) -> list[DocumentChunk]: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


@runtime_checkable
class VectorStoreProvider(Protocol):
    name: str

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None: ...

    def delete_by_source(self, source: str) -> None: ...

    def query(
        self, embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]: ...


@runtime_checkable
class Retriever(Protocol):
    name: str

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]: ...
