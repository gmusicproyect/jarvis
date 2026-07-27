"""Chunker opcional con LlamaIndex SentenceSplitter."""

from __future__ import annotations

import hashlib
import uuid

from jarvis.rag.base import DocumentChunk, RawDocument
from jarvis.rag.chunker import SlidingWindowChunker
from jarvis.utils.logging import get_logger


def build_chunker(chunk_size: int, overlap: int, *, use_llamaindex: bool = True):
    if use_llamaindex:
        try:
            return LlamaIndexChunker(chunk_size=chunk_size, overlap=overlap)
        except Exception as exc:  # noqa: BLE001
            get_logger("jarvis.rag.chunker").warning(
                "llamaindex_chunker_fallback", error=str(exc)
            )
    return SlidingWindowChunker(chunk_size=chunk_size, overlap=overlap)


class LlamaIndexChunker:
    """Usa SentenceSplitter de LlamaIndex cuando está instalado."""

    name = "llamaindex_sentence"

    def __init__(self, chunk_size: int = 800, overlap: int = 120) -> None:
        from llama_index.core.node_parser import SentenceSplitter

        self._splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, docs: list[RawDocument]) -> list[DocumentChunk]:
        from llama_index.core import Document

        out: list[DocumentChunk] = []
        for doc in docs:
            text = doc.text.strip()
            if not text:
                continue
            li_doc = Document(
                text=text,
                metadata={
                    "source": doc.source,
                    "page": "" if doc.page is None else str(doc.page),
                    **doc.metadata,
                },
            )
            nodes = self._splitter.get_nodes_from_documents([li_doc])
            for idx, node in enumerate(nodes):
                piece = node.get_content().strip()
                if not piece:
                    continue
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
                            "chunker": self.name,
                        },
                    )
                )
        return out
