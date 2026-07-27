"""Skill: buscar elemento en pantalla (visión → automatización)."""

from __future__ import annotations

import re
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.builtin._vision import get_vision
from jarvis.skills.skill import Skill
from jarvis.automation.base import ActionResult, PermissionLevel


class FindOnScreenSkill(Skill):
    name: ClassVar[str] = "find_on_screen"
    description: ClassVar[str] = (
        "Busca un botón/texto en pantalla vía OCR; puede hacer clic con confirmación"
    )
    aliases: ClassVar[list[str]] = [
        "busca el botón",
        "busca el boton",
        "localiza el botón",
        "haz clic en",
        "click en el botón",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.CONFIRM

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            [
                "busca el botón",
                "busca el boton",
                "localiza el",
                "haz clic en",
                "click en",
                "continuar",
                "aceptar",
            ],
            boost=0.9,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        vision = get_vision(ctx)
        eng = get_engine(ctx)
        if vision is None:
            return SkillResult(False, "El módulo de visión está desactivado.")
        label = self._extract_label(ctx.user_text)
        if not label:
            return SkillResult(False, "¿Qué botón o texto debo buscar?")

        want_click = any(
            k in ctx.user_text.lower() for k in ("clic", "click", "pulsa", "presiona")
        )
        matches = vision.find_on_screen(label)
        if not matches:
            return SkillResult(False, f"No encontré «{label}» en pantalla.")
        best = max(matches, key=lambda m: m.confidence)
        cx, cy = best.center
        if not want_click:
            return SkillResult(
                True,
                f"Encontré «{best.text}» en ({cx}, {cy}) "
                f"(confianza≈{best.confidence:.2f}).",
                data={"x": cx, "y": cy, "text": best.text},
            )
        if eng is None:
            return SkillResult(
                False,
                f"Encontré «{best.text}» en ({cx},{cy}) pero no hay AutomationEngine.",
            )

        def _click():
            eng.mouse.click(cx, cy)
            return ActionResult(
                True,
                f"Hice clic en «{best.text}» ({cx},{cy}).",
                "vision_click",
                PermissionLevel.CONFIRM,
                data={"x": cx, "y": cy, "label": best.text},
            )

        return result_from_action(
            eng.run(
                "vision_click",
                f"Clic en «{best.text}» en ({cx},{cy})",
                PermissionLevel.CONFIRM,
                _click,
                confirmed=ctx.confirm,
            )
        )

    def _extract_label(self, text: str) -> str | None:
        m = re.search(
            r"(?:bot[oó]n|texto|campo)\s+[«\"]?([^»\"\.]+)[»\"]?",
            text,
            re.I,
        )
        if m:
            return m.group(1).strip()
        m = re.search(r"(?:clic|click|busca|localiza)\s+(?:en\s+)?[«\"]?([^»\"]+)[»\"]?", text, re.I)
        return m.group(1).strip() if m else None
