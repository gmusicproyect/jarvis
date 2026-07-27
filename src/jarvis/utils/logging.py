"""Logging estructurado con structlog."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import structlog

from jarvis.config.loader import JarvisConfig, project_root


def _resolve_log_path(cfg: JarvisConfig) -> Path:
    root = project_root()
    path = Path(cfg.logging.file)
    if not path.is_absolute():
        path = root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging(cfg: JarvisConfig) -> None:
    """Configura logging stdlib + structlog (consola + archivo)."""
    level = getattr(logging, cfg.logging.level.upper(), logging.INFO)
    log_path = _resolve_log_path(cfg)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if cfg.logging.json_logs:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    # Archivo siempre en JSON para grep/análisis
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    file_handler.setFormatter(file_formatter)
    root.addHandler(file_handler)

    # Silenciar ruido de libs en Fase 0+
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str = "jarvis") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
