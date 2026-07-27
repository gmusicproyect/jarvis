"""Indexador incremental con hash de archivos + paralelismo."""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from jarvis.rag.base import (
    Chunker,
    DocumentLoader,
    EmbeddingProvider,
    VectorStoreProvider,
)
from jarvis.utils.logging import get_logger

SUPPORTED_SUFFIXES = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".xlsx",
    ".xlsm",
    ".pptx",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".cs",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".sql",
    ".sh",
    ".zsh",
}


class IncrementalIndexer:
    name = "incremental"

    def __init__(
        self,
        *,
        loader: DocumentLoader,
        chunker: Chunker,
        embeddings: EmbeddingProvider,
        store: VectorStoreProvider,
        index_db: Path,
        max_file_mb: float = 25.0,
        workers: int = 4,
    ) -> None:
        self.loader = loader
        self.chunker = chunker
        self.embeddings = embeddings
        self.store = store
        self.max_bytes = int(max_file_mb * 1024 * 1024)
        self.workers = max(1, workers)
        self._log = get_logger("jarvis.rag.indexer")
        self._lock = threading.Lock()
        index_db.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(index_db, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                mtime REAL NOT NULL,
                size INTEGER NOT NULL,
                indexed_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def _file_hash(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            while True:
                block = fh.read(1024 * 1024)
                if not block:
                    break
                h.update(block)
        return h.hexdigest()

    def _known(self, path: Path) -> tuple[str, float, int] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT sha256, mtime, size FROM files WHERE path=?",
                (str(path.resolve()),),
            ).fetchone()
        if not row:
            return None
        return str(row[0]), float(row[1]), int(row[2])

    def _mark(self, path: Path, sha: str, mtime: float, size: int) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO files(path, sha256, mtime, size, indexed_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(path) DO UPDATE SET
                  sha256=excluded.sha256,
                  mtime=excluded.mtime,
                  size=excluded.size,
                  indexed_at=excluded.indexed_at
                """,
                (str(path.resolve()), sha, mtime, size, time.time()),
            )
            self._conn.commit()

    def _needs_index(self, path: Path) -> bool:
        st = path.stat()
        if st.st_size > self.max_bytes:
            self._log.warning("skip_too_large", path=str(path), size=st.st_size)
            return False
        known = self._known(path)
        if known is None:
            return True
        sha_old, mtime_old, size_old = known
        if size_old == st.st_size and abs(mtime_old - st.st_mtime) < 0.01:
            # mtime+size iguales → sin cambio (evita hashear siempre)
            return False
        sha = self._file_hash(path)
        return sha != sha_old

    def _index_one(self, path: Path) -> dict[str, object]:
        t0 = time.perf_counter()
        source = str(path.resolve())
        docs = self.loader.load(path)
        chunks = self.chunker.chunk(docs)
        if not chunks:
            return {"path": source, "chunks": 0, "skipped": False}
        self.store.delete_by_source(source)
        embeddings = self.embeddings.embed_documents([c.text for c in chunks])
        self.store.upsert(chunks, embeddings)
        sha = self._file_hash(path)
        st = path.stat()
        self._mark(path, sha, st.st_mtime, st.st_size)
        elapsed = (time.perf_counter() - t0) * 1000
        self._log.info(
            "file_indexed",
            path=source,
            chunks=len(chunks),
            elapsed_ms=round(elapsed, 1),
        )
        return {"path": source, "chunks": len(chunks), "skipped": False}

    def collect_files(self, root: Path) -> list[Path]:
        root = root.expanduser().resolve()
        if root.is_file():
            return [root] if root.suffix.lower() in SUPPORTED_SUFFIXES else []
        files: list[Path] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            if any(part.startswith(".") for part in path.parts):
                continue
            files.append(path)
        return files

    def index_path(self, root: Path, *, force: bool = False) -> dict[str, object]:
        files = self.collect_files(root)
        to_process = [p for p in files if force or self._needs_index(p)]
        skipped = len(files) - len(to_process)
        results: list[dict[str, object]] = []
        errors: list[str] = []

        def _job(p: Path) -> dict[str, object]:
            return self._index_one(p)

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futs = {pool.submit(_job, p): p for p in to_process}
            for fut in as_completed(futs):
                path = futs[fut]
                try:
                    results.append(fut.result())
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{path}: {exc}")
                    self._log.warning("index_error", path=str(path), error=str(exc))

        total_chunks = sum(int(r.get("chunks", 0)) for r in results)
        return {
            "files_seen": len(files),
            "indexed": len(results),
            "skipped_unchanged": skipped,
            "chunks": total_chunks,
            "errors": errors,
        }
