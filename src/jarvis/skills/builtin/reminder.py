"""Recordatorios integrados con memoria persistente."""

from __future__ import annotations

import re
from typing import ClassVar

from jarvis.memory.base import MemoryKind
from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill


class ReminderSkill(Skill):
    name: ClassVar[str] = "reminder"
    description: ClassVar[str] = "Crea recordatorios en la memoria persistente"
    aliases: ClassVar[list[str]] = ["recuérdame", "recuerdame", "recordatorio", "avísame"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            ["recuerdame", "recuérdame", "recordatorio", "avisame", "avísame mañana"],
            boost=0.94,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        if ctx.memory is None:
            return SkillResult(False, "La memoria no está disponible.")
        m = re.search(
            r"(?:recuerdame|recuérdame|avisame|avísame|recordatorio)\s+(.+)$",
            ctx.user_text,
            re.I,
        )
        payload = m.group(1).strip(" .") if m else ctx.user_text
        item = ctx.memory.persistent.add_item(
            MemoryKind.REMINDER, payload, title="recordatorio"
        )
        if ctx.memory.semantic:
            ctx.memory._index(item)  # noqa: SLF001
        return SkillResult(
            True,
            f"Recordatorio guardado: {payload}.",
            data={"id": item.id},
        )
