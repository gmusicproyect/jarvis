"""Skill: describe / resume lo que hay en pantalla."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.builtin._vision import analysis_result, get_vision
from jarvis.skills.skill import Skill
from jarvis.vision.base import CaptureMode


class DescribeScreenSkill(Skill):
    name: ClassVar[str] = "describe_screen"
    description: ClassVar[str] = "Describe o resume lo que aparece en la pantalla"
    aliases: ClassVar[list[str]] = [
        "qué hay en mi pantalla",
        "que hay en mi pantalla",
        "describe la pantalla",
        "qué aparece en mi pantalla",
        "resume esta captura",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            [
                "pantalla",
                "captura",
                "qué hay en mi",
                "que hay en mi",
                "describe la pantalla",
                "qué aparece",
                "que aparece",
                "resume esta captura",
                "qué error aparece",
                "que error aparece",
            ],
            boost=0.93,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        vision = get_vision(ctx)
        if vision is None:
            return SkillResult(False, "El módulo de visión está desactivado.")
        mode = CaptureMode.FULL
        low = ctx.user_text.lower()
        if "ventana" in low or "activa" in low:
            mode = CaptureMode.ACTIVE_WINDOW
        try:
            analysis = vision.describe_screen(ctx.user_text, mode=mode)
            return analysis_result(analysis)
        except Exception as exc:  # noqa: BLE001
            return SkillResult(False, "No pude analizar la pantalla.", error=str(exc))
