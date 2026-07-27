"""Skill: portapapeles."""

from __future__ import annotations

import re
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import norm, score_keywords
from jarvis.skills.skill import Skill


class ClipboardSkill(Skill):
    name: ClassVar[str] = "clipboard"
    description: ClassVar[str] = "Lee o escribe texto en el portapapeles"
    aliases: ClassVar[list[str]] = [
        "portapapeles",
        "copia esto",
        "copia al portapapeles",
        "pega",
        "qué hay en el portapapeles",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        n = norm(text)
        if "portapapeles" in n or "clipboard" in n:
            return 0.95
        if n.startswith("copia ") or "copia este" in n or "copia esto" in n:
            return 0.9
        return score_keywords(text, ["copia al porta", "lee el porta"], boost=0.85)

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        if eng is None:
            return SkillResult(False, "AutomationEngine no disponible.")
        n = norm(ctx.user_text)
        if any(k in n for k in ("lee", "leer", "que hay", "qué hay", "muestra")):
            return result_from_action(eng.clipboard_read())

        # extraer texto a copiar
        if ":" in ctx.user_text:
            text = ctx.user_text.split(":", 1)[1].strip()
        else:
            m = re.search(
                r"copia(?:r)?(?:\s+(?:esto|este\s+texto))?\s+"
                r"(?:al\s+portapapeles\s+)?(.+)$",
                ctx.user_text,
                re.I,
            )
            text = m.group(1).strip() if m else ""
            if text.lower().startswith("al portapapeles"):
                text = text.split("al portapapeles", 1)[-1].strip(" :")
        if not text or text.lower() in {"esto", "este texto", "al portapapeles"}:
            return SkillResult(False, "¿Qué texto quieres copiar al portapapeles?")
        return result_from_action(eng.clipboard_write(text))
