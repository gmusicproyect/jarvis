"""Skill: gestión de ventanas."""

from __future__ import annotations

import re
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import norm, score_keywords
from jarvis.skills.skill import Skill


class WindowManagerSkill(Skill):
    name: ClassVar[str] = "window_manager"
    description: ClassVar[str] = "Cambia el foco entre ventanas o las minimiza"
    aliases: ClassVar[list[str]] = [
        "cambia el foco",
        "enfoca",
        "minimiza",
        "trae al frente",
        "lista ventanas",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        n = norm(text)
        if any(k in n for k in ("foco", "ventana", "minimiza", "al frente")):
            return 0.9
        return score_keywords(text, ["cambia el foco", "enfoca", "minimiza"], boost=0.85)

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        if eng is None:
            return SkillResult(False, "AutomationEngine no disponible.")
        n = norm(ctx.user_text)
        if "lista" in n and "ventana" in n:
            wins = eng.windows.list_windows()
            preview = ", ".join(wins[:12]) if wins else "(ninguna)"
            return SkillResult(True, f"Ventanas: {preview}", data={"windows": wins})

        if "minimiza" in n:
            m = re.search(r"minimiza\s+(.+)$", ctx.user_text, re.I)
            target = m.group(1).strip() if m else None
            from jarvis.automation.base import ActionResult, PermissionLevel

            def _min():
                eng.windows.minimize(target)
                return ActionResult(
                    True,
                    f"Minimizando {target or 'ventana actual'}.",
                    "minimize",
                    PermissionLevel.SAFE,
                )

            return result_from_action(
                eng.run(
                    "minimize",
                    f"Minimizar {target or 'ventana'}",
                    PermissionLevel.SAFE,
                    _min,
                    confirmed=ctx.confirm,
                )
            )

        m = re.search(
            r"(?:foco|enfoca|trae al frente|activa)\s+(?:a\s+|en\s+|de\s+)?(.+)$",
            ctx.user_text,
            re.I,
        )
        target = m.group(1).strip() if m else None
        if not target:
            return SkillResult(False, "¿A qué ventana o aplicación cambio el foco?")
        return result_from_action(eng.focus_window(target))
