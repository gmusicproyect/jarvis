"""Abrir sitios web — vía AutomationEngine / browser."""

from __future__ import annotations

from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import extract_url, norm
from jarvis.skills.builtin.browser import BrowserSkill
from jarvis.skills.skill import Skill


class OpenUrlSkill(Skill):
    name: ClassVar[str] = "open_url"
    description: ClassVar[str] = "Abre una URL o sitio web en el navegador"
    aliases: ClassVar[list[str]] = ["abre web", "abre la pagina", "abre sitio"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def __init__(self) -> None:
        self._browser = BrowserSkill()

    def can_handle(self, text: str) -> float:
        n = norm(text)
        url = extract_url(text)
        if url:
            return 0.97
        # cede a browser para openai/google/manual
        if any(k in n for k in ("openai", "manual", "staging", "google", "chatgpt")):
            return 0.4
        if any(w in n for w in ("http", "www", "pagina", "sitio", "web", "navegador")):
            if any(w in n for w in ("abre", "abrir", "ve a", "visita")):
                return 0.85
        return 0.0

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        url = extract_url(ctx.user_text)
        if eng is not None and url:
            return result_from_action(eng.open_url(url, confirmed=ctx.confirm))
        return self._browser.execute(ctx)
