"""Temporizadores en segundo plano."""

from __future__ import annotations

import threading
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import extract_minutes, score_keywords
from jarvis.skills.skill import Skill

_TIMERS: list[threading.Timer] = []


class TimerSkill(Skill):
    name: ClassVar[str] = "timer"
    description: ClassVar[str] = "Programa un temporizador"
    aliases: ClassVar[list[str]] = ["temporizador", "timer", "cuenta atras", "pon un timer"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        if extract_minutes(text) and score_keywords(
            text, ["temporizador", "timer", "cuenta", "alarma", "avisa en"], boost=0.5
        ):
            return 0.93
        return score_keywords(
            text, ["temporizador", "timer", "pon un timer", "cuenta atras"], boost=0.88
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        minutes = extract_minutes(ctx.user_text) or 5
        seconds = max(1, minutes * 60)

        def _fire() -> None:
            # Señal en logs; la UI/voz de aviso completo llega en fases posteriores
            from jarvis.utils.logging import get_logger

            get_logger("jarvis.timer").info("timer_done", minutes=minutes)

        timer = threading.Timer(seconds, _fire)
        timer.daemon = True
        timer.start()
        _TIMERS.append(timer)
        return SkillResult(
            True,
            f"Temporizador de {minutes} minuto(s) activado.",
            data={"minutes": minutes, "seconds": seconds},
        )
