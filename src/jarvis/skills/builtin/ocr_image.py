"""Skill: OCR de imagen o pantalla."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.builtin._vision import analysis_result, extract_image_path, get_vision
from jarvis.skills.skill import Skill


class OcrImageSkill(Skill):
    name: ClassVar[str] = "ocr_image"
    description: ClassVar[str] = "Extrae texto (OCR) de una imagen o de la pantalla"
    aliases: ClassVar[list[str]] = [
        "lee el texto",
        "ocr",
        "extrae el texto",
        "qué texto hay",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            ["ocr", "lee el texto", "extrae el texto", "texto de esta imagen", "lee esta imagen"],
            boost=0.94,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        vision = get_vision(ctx)
        if vision is None:
            return SkillResult(False, "El módulo de visión está desactivado.")
        path = extract_image_path(ctx.user_text)
        try:
            analysis = vision.ocr_only(path)
            return analysis_result(analysis)
        except Exception as exc:  # noqa: BLE001
            return SkillResult(False, "No pude hacer OCR.", error=str(exc))
