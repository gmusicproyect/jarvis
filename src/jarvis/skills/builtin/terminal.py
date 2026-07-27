"""Skill: terminal / shell con allowlist."""

from __future__ import annotations

import re
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import norm, score_keywords
from jarvis.skills.skill import Skill


class TerminalSkill(Skill):
    name: ClassVar[str] = "terminal"
    description: ClassVar[str] = "Ejecuta comandos de terminal permitidos (con confirmación)"
    aliases: ClassVar[list[str]] = [
        "ejecuta el comando",
        "corre el comando",
        "en la terminal",
        "shell",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.CONFIRM

    def can_handle(self, text: str) -> float:
        n = norm(text)
        if any(k in n for k in ("terminal", "comando", "shell", "bash")):
            return 0.9
        return score_keywords(text, ["ejecuta el comando", "corre el comando"], boost=0.88)

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        if eng is None:
            return SkillResult(False, "AutomationEngine no disponible.")
        m = re.search(
            r"(?:comando|shell|terminal|ejecuta|corre)\s*[:\-]?\s*(.+)$",
            ctx.user_text,
            re.I,
        )
        command = m.group(1).strip().strip("«»\"'") if m else ""
        if not command:
            return SkillResult(False, "¿Qué comando debo ejecutar?")
        # riesgo dinámico
        low = command.lower()
        if any(x in low for x in ("rm ", "sudo", "diskutil", "mkfs")):
            self.required_permissions = RiskLevel.RESTRICTED  # type: ignore[misc]
        return result_from_action(eng.run_shell(command, confirmed=ctx.confirm))
