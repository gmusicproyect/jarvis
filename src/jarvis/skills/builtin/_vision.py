"""Helpers skills de visión."""

from __future__ import annotations

from pathlib import Path
import re

from jarvis.skills.base import SkillContext, SkillResult
from jarvis.vision.orchestrator import VisionOrchestrator


def get_vision(ctx: SkillContext) -> VisionOrchestrator | None:
    v = ctx.config.get("vision")
    return v if isinstance(v, VisionOrchestrator) else None


def extract_image_path(text: str) -> Path | None:
    m = re.search(
        r"(/[^\s]+\.(?:png|jpe?g|webp|gif|bmp)|~/[^\s]+\.(?:png|jpe?g|webp|gif|bmp))",
        text,
        re.I,
    )
    if not m:
        return None
    return Path(m.group(1)).expanduser()


def analysis_result(analysis, prefix: str = "") -> SkillResult:  # noqa: ANN001
    msg = analysis.answer
    if prefix:
        msg = f"{prefix}{msg}"
    return SkillResult(
        True,
        msg,
        data={
            "image": str(analysis.image_path),
            "tags": analysis.tags,
            "ocr_confidence": analysis.ocr.confidence if analysis.ocr else None,
            "vision_model": analysis.vision.model if analysis.vision else None,
            "elapsed_ms": analysis.elapsed_ms,
            "history_id": analysis.history_id,
        },
    )
