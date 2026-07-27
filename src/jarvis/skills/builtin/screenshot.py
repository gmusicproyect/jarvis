"""Skill: captura de pantalla."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill


class ScreenshotSkill(Skill):
    name: ClassVar[str] = "screenshot"
    description: ClassVar[str] = "Toma una captura de pantalla"
    aliases: ClassVar[list[str]] = [
        "captura de pantalla",
        "screenshot",
        "haz una captura",
        "toma una captura",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            ["captura", "screenshot", "pantallazo", "haz una captura"],
            boost=0.94,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        if eng is None:
            return SkillResult(False, "AutomationEngine no disponible.")
        return result_from_action(eng.take_screenshot())
