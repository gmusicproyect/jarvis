"""Factory RAG a partir de config."""

from __future__ import annotations

from pathlib import Path

from jarvis.config.loader import JarvisConfig, project_root
from jarvis.llm.ollama import OllamaProvider
from jarvis.rag.embeddings import OllamaEmbeddingProvider
from jarvis.rag.indexer import IncrementalIndexer
from jarvis.rag.llamaindex_chunker import build_chunker
from jarvis.rag.loaders import CompositeLoader
from jarvis.rag.orchestrator import RAGOrchestrator
from jarvis.rag.retriever import SimilarityRetriever
from jarvis.rag.vectorstore import ChromaVectorStore


def _resolve(root: Path, maybe: str) -> Path:
    path = Path(maybe)
    return path if path.is_absolute() else root / path


def build_rag_stack(cfg: JarvisConfig) -> tuple[IncrementalIndexer, RAGOrchestrator]:
    root = project_root()
    rag = cfg.rag

    embeddings = OllamaEmbeddingProvider(
        model=rag.embedding_model,
        base_url=rag.embedding_base_url or cfg.llm.base_url,
        cache_path=_resolve(root, "data/db/emb_cache.db")
        if rag.cache_embeddings
        else None,
        enabled_cache=rag.cache_embeddings,
    )
    store = ChromaVectorStore(
        _resolve(root, rag.chroma_dir),
        collection=rag.collection,
    )
    chunker = build_chunker(
        rag.chunk_size,
        rag.chunk_overlap,
        use_llamaindex=rag.use_llamaindex_splitter,
    )
    loader = CompositeLoader()
    indexer = IncrementalIndexer(
        loader=loader,
        chunker=chunker,
        embeddings=embeddings,
        store=store,
        index_db=_resolve(root, rag.index_db),
        max_file_mb=rag.max_file_mb,
        workers=rag.parallel_workers,
    )
    retriever = SimilarityRetriever(embeddings, store)
    llm = OllamaProvider(cfg.llm)
    orch = RAGOrchestrator(
        retriever,
        llm,
        top_k=rag.top_k,
        min_score=rag.min_score,
        refuse_if_insufficient=rag.refuse_if_insufficient,
        user_name=cfg.app.user_name,
    )
    return indexer, orch
