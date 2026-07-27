"""Watcher opcional de knowledge/ con watchdog."""

from __future__ import annotations

import time
from pathlib import Path

from jarvis.rag.indexer import IncrementalIndexer
from jarvis.utils.logging import get_logger


class KnowledgeWatcher:
    """Observa una carpeta y reindexa cambios. Requiere paquete watchdog."""

    def __init__(self, folder: Path, indexer: IncrementalIndexer) -> None:
        self.folder = folder.expanduser().resolve()
        self.indexer = indexer
        self._log = get_logger("jarvis.rag.watcher")
        self._observer = None

    def start(self) -> None:
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError as exc:
            raise RuntimeError(
                "Instala watchdog para el watcher: poetry add watchdog"
            ) from exc

        indexer = self.indexer
        log = self._log
        folder = self.folder
        folder.mkdir(parents=True, exist_ok=True)

        class Handler(FileSystemEventHandler):
            def on_created(self, event):  # type: ignore[no-untyped-def]
                if event.is_directory:
                    return
                log.info("watch_created", path=event.src_path)
                indexer.index_path(Path(event.src_path))

            def on_modified(self, event):  # type: ignore[no-untyped-def]
                if event.is_directory:
                    return
                log.info("watch_modified", path=event.src_path)
                indexer.index_path(Path(event.src_path))

        observer = Observer()
        observer.schedule(Handler(), str(folder), recursive=True)
        observer.start()
        self._observer = observer
        self._log.info("watcher_started", folder=str(folder))

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._log.info("watcher_stopped")

    def run_forever(self) -> None:
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
