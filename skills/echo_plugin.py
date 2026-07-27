"""Plugin de ejemplo: eco — demuestra carga dinámica sin tocar el núcleo."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.skill import Skill


class EchoSkill(Skill):
    name: ClassVar[str] = "echo_plugin"
    description: ClassVar[str] = "Repite el texto tras la palabra eco"
    aliases: ClassVar[list[str]] = ["eco", "repite plugin"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return 0.99 if text.lower().startswith("eco ") else 0.0

    def execute(self, ctx: SkillContext) -> SkillResult:
        payload = ctx.user_text[4:].strip()
        return SkillResult(True, payload or "No hay nada que repetir.")
