"""Skill: lee / resume la pantalla (visión + OCR)."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.builtin._vision import analysis_result, get_vision
from jarvis.skills.skill import Skill
from jarvis.vision.base import CaptureMode


class ReadScreenSkill(Skill):
    name: ClassVar[str] = "read_screen"
    description: ClassVar[str] = "Lee el contenido de la pantalla (OCR + visión)"
    aliases: ClassVar[list[str]] = [
        "lee la pantalla",
        "lee mi pantalla",
        "qué pone en pantalla",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            ["lee la pantalla", "lee mi pantalla", "qué pone en", "que pone en"],
            boost=0.92,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        vision = get_vision(ctx)
        if vision is None:
            return SkillResult(False, "El módulo de visión está desactivado.")
        try:
            analysis = vision.describe_screen(
                ctx.user_text or "Lee el contenido de la pantalla.",
                mode=CaptureMode.FULL,
            )
            return analysis_result(analysis)
        except Exception as exc:  # noqa: BLE001
            return SkillResult(False, "No pude leer la pantalla.", error=str(exc))
