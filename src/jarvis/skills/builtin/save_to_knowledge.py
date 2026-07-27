"""Skill: guardar última captura/análisis en knowledge (RAG)."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.builtin._vision import get_vision
from jarvis.skills.skill import Skill


class SaveToKnowledgeSkill(Skill):
    name: ClassVar[str] = "save_to_knowledge"
    description: ClassVar[str] = (
        "Guarda la última captura/análisis visual en la base de conocimiento (RAG)"
    )
    aliases: ClassVar[list[str]] = [
        "guarda esta captura",
        "guarda en mi base",
        "indexa esta captura",
        "guarda en conocimiento",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            [
                "guarda esta captura",
                "guarda en mi base",
                "base de conocimiento",
                "indexa esta captura",
                "guarda en conocimiento",
                "guarda la captura",
            ],
            boost=0.95,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        vision = get_vision(ctx)
        if vision is None:
            return SkillResult(False, "El módulo de visión está desactivado.")
        try:
            if vision.last_analysis is None:
                # capturar y analizar primero
                vision.describe_screen("Resume esta captura para guardar en conocimiento.")
            path = vision.save_to_knowledge(title="Captura Jarvis")
            return SkillResult(
                True,
                f"Guardé e indexé la captura en {path.name}.",
                data={"path": str(path)},
            )
        except Exception as exc:  # noqa: BLE001
            return SkillResult(
                False, "No pude guardar en la base de conocimiento.", error=str(exc)
            )
