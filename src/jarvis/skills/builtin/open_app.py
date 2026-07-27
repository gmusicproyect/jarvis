"""Abrir aplicaciones — delega en open_application (compat)."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin.open_application import OpenApplicationSkill
from jarvis.skills.skill import Skill


class OpenAppSkill(Skill):
    """Compatibilidad con el nombre histórico ``open_app``."""

    name: ClassVar[str] = "open_app"
    description: ClassVar[str] = "Alias de open_application"
    aliases: ClassVar[list[str]] = []
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def __init__(self) -> None:
        self._inner = OpenApplicationSkill()

    def can_handle(self, text: str) -> float:
        # Alias de compatibilidad: cede prioridad a open_application.
        return min(0.7, self._inner.can_handle(text) * 0.72)

    def execute(self, ctx: SkillContext) -> SkillResult:
        return self._inner.execute(ctx)
