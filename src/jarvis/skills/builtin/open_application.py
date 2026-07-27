"""Skill: abrir / cerrar aplicaciones (vía AutomationEngine)."""

from __future__ import annotations

import re
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import APP_MAP, get_engine, result_from_action
from jarvis.skills.builtin._text import norm, score_keywords
from jarvis.skills.skill import Skill


class OpenApplicationSkill(Skill):
    name: ClassVar[str] = "open_application"
    description: ClassVar[str] = "Abre o cierra aplicaciones del sistema"
    aliases: ClassVar[list[str]] = [
        "abre",
        "abrir",
        "cierra",
        "cerrar",
        "lanza",
        "visual studio",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        n = norm(text)
        if any(x in n for x in ("http", ".com", "navegador", "pagina", "sitio", "google")):
            if "abre" in n and any(k in n for k in APP_MAP if k != "openai"):
                pass
            else:
                return 0.15
        if "cierra" in n or "cerrar" in n:
            return 0.88
        if not any(a in n for a in ("abre", "abrir", "lanza", "ejecuta")):
            return 0.0
        if any(k in n for k in APP_MAP if APP_MAP[k]):
            return 0.96
        return score_keywords(text, ["abre", "abrir", "aplicacion", "app"], boost=0.65)

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        if eng is None:
            return SkillResult(False, "AutomationEngine no disponible.")
        n = norm(ctx.user_text)
        app = None
        for key, value in APP_MAP.items():
            if value and key in n:
                app = value
                break
        if app is None:
            m = re.search(
                r"(?:abre|abrir|lanza|ejecuta|cierra|cerrar)\s+"
                r"(?:la\s+app\s+|el\s+|la\s+)?(.+)$",
                ctx.user_text,
                re.I,
            )
            app = m.group(1).strip(" .") if m else None
        if not app:
            return SkillResult(False, "¿Qué aplicación quieres controlar?")

        if "cierra" in n or "cerrar" in n:
            from jarvis.automation.base import PermissionLevel

            def _close():
                eng.apps.close_app(app)
                from jarvis.automation.base import ActionResult

                return ActionResult(
                    True,
                    f"Cerrando {app}.",
                    "close_application",
                    PermissionLevel.SAFE,
                    data={"app": app},
                )

            return result_from_action(
                eng.run(
                    "close_application",
                    f"Cerrar aplicación «{app}»",
                    PermissionLevel.SAFE,
                    _close,
                    confirmed=ctx.confirm,
                )
            )
        return result_from_action(eng.open_application(app, confirmed=ctx.confirm))
