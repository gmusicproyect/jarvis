"""Embeddings Ollama con caché local opcional."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import httpx

from jarvis.utils.logging import get_logger


class OllamaEmbeddingProvider:
    name = "ollama"

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        cache_path: Path | None = None,
        enabled_cache: bool = True,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._log = get_logger("jarvis.rag.embed")
        self._cache_enabled = enabled_cache and cache_path is not None
        self._conn: sqlite3.Connection | None = None
        if self._cache_enabled and cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(cache_path, check_same_thread=False)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS emb_cache (
                    key TEXT PRIMARY KEY,
                    vector TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self.model}:{text}".encode()).hexdigest()

    def _cache_get(self, text: str) -> list[float] | None:
        if not self._conn:
            return None
        row = self._conn.execute(
            "SELECT vector FROM emb_cache WHERE key=?", (self._key(text),)
        ).fetchone()
        if not row:
            return None
        return list(json.loads(row[0]))

    def _cache_set(self, text: str, vector: list[float]) -> None:
        if not self._conn:
            return
        self._conn.execute(
            "INSERT OR REPLACE INTO emb_cache(key, vector) VALUES(?,?)",
            (self._key(text), json.dumps(vector)),
        )
        self._conn.commit()

    def _embed_one(self, text: str) -> list[float]:
        cached = self._cache_get(text)
        if cached is not None:
            return cached
        with httpx.Client(base_url=self.base_url, timeout=120.0) as client:
            resp = client.post("/api/embed", json={"model": self.model, "input": text})
            if resp.status_code == 404:
                resp = client.post(
                    "/api/embeddings", json={"model": self.model, "prompt": text}
                )
            resp.raise_for_status()
            data = resp.json()
            if "embeddings" in data and data["embeddings"]:
                vec = list(data["embeddings"][0])
            else:
                vec = list(data["embedding"])
        self._cache_set(text, vec)
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)
