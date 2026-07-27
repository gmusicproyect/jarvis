"""Contrato Skill + helper base."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult


class Skill(ABC):
    """Interfaz común — toda skill debe heredar de esta clase."""

    name: ClassVar[str]
    description: ClassVar[str]
    aliases: ClassVar[list[str]] = []
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    @abstractmethod
    def can_handle(self, text: str) -> float:
        """Confianza 0.0–1.0 de que esta skill aplica."""

    @abstractmethod
    def execute(self, ctx: SkillContext) -> SkillResult:
        """Ejecuta la acción."""

    def matches_alias(self, text: str) -> bool:
        lowered = text.lower()
        return any(a.lower() in lowered for a in self.aliases)
