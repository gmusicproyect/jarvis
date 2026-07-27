"""Fecha y hora actuales."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill

_DAYS = {
    "Monday": "lunes",
    "Tuesday": "martes",
    "Wednesday": "miércoles",
    "Thursday": "jueves",
    "Friday": "viernes",
    "Saturday": "sábado",
    "Sunday": "domingo",
}
_MONTHS = {
    "January": "enero",
    "February": "febrero",
    "March": "marzo",
    "April": "abril",
    "May": "mayo",
    "June": "junio",
    "July": "julio",
    "August": "agosto",
    "September": "septiembre",
    "October": "octubre",
    "November": "noviembre",
    "December": "diciembre",
}


class DateTimeSkill(Skill):
    name: ClassVar[str] = "datetime"
    description: ClassVar[str] = "Dice la fecha y/o la hora actual"
    aliases: ClassVar[list[str]] = ["qué hora", "que hora", "qué día", "fecha", "hora"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            ["hora", "fecha", "dia", "qué dia", "que dia", "hoy es"],
            boost=0.9,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        now = datetime.now()
        day = _DAYS[now.strftime("%A")]
        month = _MONTHS[now.strftime("%B")]
        msg = (
            f"Son las {now.strftime('%H:%M')} del {day} "
            f"{now.day} de {month} de {now.year}."
        )
        return SkillResult(True, msg, data={"iso": now.isoformat()})
