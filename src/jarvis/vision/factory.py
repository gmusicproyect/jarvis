"""Factory del stack de visión."""

from __future__ import annotations

from pathlib import Path

from jarvis.config.loader import JarvisConfig, project_root
from jarvis.vision.analyzer import DefaultImageAnalyzer
from jarvis.vision.history import VisionHistory
from jarvis.vision.ocr import build_ocr_provider
from jarvis.vision.orchestrator import VisionOrchestrator
from jarvis.vision.providers import build_vision_provider
from jarvis.vision.screen import build_screen_provider
from jarvis.utils.logging import get_logger


def _resolve(root: Path, maybe: str) -> Path:
    path = Path(maybe)
    return path if path.is_absolute() else root / path


def build_vision_stack(cfg: JarvisConfig) -> VisionOrchestrator | None:
    if not cfg.vision.enabled:
        return None
    root = project_root()
    v = cfg.vision
    log = get_logger("jarvis.vision.factory")

    ocr = build_ocr_provider(v.ocr_provider, v.ocr_languages)
    vision = build_vision_provider(
        v.provider,
        model=v.model,
        base_url=v.base_url or cfg.llm.base_url,
        api_key=None,  # lee de env
    )
    analyzer = DefaultImageAnalyzer(ocr, vision)
    history = (
        VisionHistory(_resolve(root, v.history_db)) if v.history_enabled else None
    )
    orch = VisionOrchestrator(
        screen=build_screen_provider(),
        analyzer=analyzer,
        history=history,
        captures_dir=_resolve(root, v.captures_dir),
        knowledge_dir=_resolve(root, cfg.rag.knowledge_dir),
        user_name=cfg.app.user_name,
    )
    log.info(
        "vision_ready",
        ocr=ocr.name,
        vision=vision.name,
        model=getattr(vision, "model", ""),
        history=v.history_enabled,
    )
    return orch
