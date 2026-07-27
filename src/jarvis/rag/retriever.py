"""Retriever sobre embeddings + vector store."""

from __future__ import annotations

from jarvis.rag.base import EmbeddingProvider, RetrievedChunk, VectorStoreProvider


class SimilarityRetriever:
    name = "similarity"

    def __init__(
        self,
        embeddings: EmbeddingProvider,
        store: VectorStoreProvider,
    ) -> None:
        self._emb = embeddings
        self._store = store

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        vector = self._emb.embed_query(query)
        return self._store.query(vector, top_k=top_k)
