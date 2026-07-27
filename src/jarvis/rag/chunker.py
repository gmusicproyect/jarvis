"""Chunker de texto con tamaño y overlap configurables."""

from __future__ import annotations

import hashlib
import uuid

from jarvis.rag.base import DocumentChunk, RawDocument


class SlidingWindowChunker:
    name = "sliding_window"

    def __init__(self, chunk_size: int = 800, overlap: int = 120) -> None:
        self.chunk_size = max(200, chunk_size)
        self.overlap = max(0, min(overlap, self.chunk_size // 2))

    def chunk(self, docs: list[RawDocument]) -> list[DocumentChunk]:
        out: list[DocumentChunk] = []
        for doc in docs:
            text = " ".join(doc.text.split())
            if not text:
                continue
            start = 0
            idx = 0
            while start < len(text):
                end = min(len(text), start + self.chunk_size)
                piece = text[start:end].strip()
                if piece:
                    digest = hashlib.sha1(
                        f"{doc.source}:{doc.page}:{idx}:{piece[:64]}".encode()
                    ).hexdigest()[:16]
                    out.append(
                        DocumentChunk(
                            id=f"{digest}-{uuid.uuid4().hex[:8]}",
                            text=piece,
                            source=doc.source,
                            page=doc.page,
                            metadata={
                                **doc.metadata,
                                "chunk_index": str(idx),
                            },
                        )
                    )
                    idx += 1
                if end >= len(text):
                    break
                start = end - self.overlap
        return out
