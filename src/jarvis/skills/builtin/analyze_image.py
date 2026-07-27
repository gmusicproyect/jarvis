"""Skill: analiza una imagen concreta (ruta o última captura)."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.builtin._vision import (
    analysis_result,
    extract_image_path,
    get_vision,
)
from jarvis.skills.skill import Skill


class AnalyzeImageSkill(Skill):
    name: ClassVar[str] = "analyze_image"
    description: ClassVar[str] = "Analiza una imagen (ruta) con OCR y visión"
    aliases: ClassVar[list[str]] = [
        "analiza esta imagen",
        "describe esta imagen",
        "qué hay en esta imagen",
        "qué botones ves",
        "hay una tabla",
        "describe este gráfico",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            [
                "esta imagen",
                "analiza la imagen",
                "qué botones",
                "que botones",
                "hay una tabla",
                "describe este grafico",
                "describe este gráfico",
                ".png",
                ".jpg",
                ".jpeg",
            ],
            boost=0.9,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        vision = get_vision(ctx)
        if vision is None:
            return SkillResult(False, "El módulo de visión está desactivado.")
        path = extract_image_path(ctx.user_text)
        if path is None and vision.last_analysis is not None:
            path = vision.last_analysis.image_path
        if path is None or not path.exists():
            return SkillResult(
                False,
                "Indica la ruta de la imagen o captura la pantalla primero.",
            )
        try:
            analysis = vision.analyze_image(path, ctx.user_text, source="file")
            return analysis_result(analysis)
        except Exception as exc:  # noqa: BLE001
            return SkillResult(False, "No pude analizar la imagen.", error=str(exc))
