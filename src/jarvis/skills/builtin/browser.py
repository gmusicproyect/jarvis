"""Skill: navegador (URL, Google, RAG→URL)."""

from __future__ import annotations

import re
from typing import ClassVar
from urllib.parse import urlparse

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import extract_url, norm, score_keywords
from jarvis.skills.skill import Skill

_SITE_MAP = {
    "openai": "https://chatgpt.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
}


def _extract_url_from_text(text: str) -> str | None:
    urls = re.findall(r"https?://[^\s\]\)\"']+", text)
    if urls:
        return urls[0].rstrip(".,;)")
    # staging.example.com style
    m = re.search(r"\b([a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?)\b", text, re.I)
    if m and " " not in m.group(1):
        host = m.group(1)
        if any(x in host for x in (".", "localhost")):
            return "https://" + host if not host.startswith("http") else host
    return None


class BrowserSkill(Skill):
    name: ClassVar[str] = "browser"
    description: ClassVar[str] = (
        "Abre URLs, busca en Google o navega a una URL encontrada en documentos (RAG)"
    )
    aliases: ClassVar[list[str]] = [
        "abre en el navegador",
        "busca en google",
        "abre openai",
        "navega",
        "abre la url",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        n = norm(text)
        if "manual" in n and ("url" in n or "abre" in n or "staging" in n or "servidor" in n):
            return 0.97
        if any(k in n for k in ("navegador", "google", "openai", "chatgpt", "pagina web")):
            return 0.92
        if extract_url(text):
            return 0.9
        if "busca en google" in n or "buscar en google" in n:
            return 0.95
        return score_keywords(
            text,
            ["abre openai", "abre github", "abre youtube", "en el navegador"],
            boost=0.85,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        if eng is None:
            return SkillResult(False, "AutomationEngine no disponible.")

        n = norm(ctx.user_text)
        url = extract_url(ctx.user_text)

        # RAG: buscar URL en documentos
        if url is None and any(
            k in n
            for k in (
                "manual",
                "documento",
                "staging",
                "produccion",
                "producción",
                "servidor",
            )
        ):
            url = self._url_from_rag(ctx)
            if not url:
                return SkillResult(
                    False,
                    "No encontré una URL en tus documentos. Indexa el manual e inténtalo de nuevo.",
                )

        if url is None:
            for key, site in _SITE_MAP.items():
                if key in n and "busca" not in n:
                    url = site
                    break

        if url is None and ("google" in n or "busca" in n):
            m = re.search(
                r"(?:busca(?:r)?(?:\s+en\s+google)?|google)\s+(.+)$",
                ctx.user_text,
                re.I,
            )
            query = m.group(1).strip() if m else ctx.user_text

            def _search():
                from jarvis.automation.base import ActionResult, PermissionLevel

                eng.browser.search_google(query)
                return ActionResult(
                    True,
                    f"Buscando en Google: {query}.",
                    "search_google",
                    PermissionLevel.SAFE,
                    data={"query": query},
                )

            from jarvis.automation.base import PermissionLevel

            return result_from_action(
                eng.run(
                    "search_google",
                    f"Buscar en Google: {query}",
                    PermissionLevel.SAFE,
                    _search,
                    confirmed=ctx.confirm,
                )
            )

        if not url:
            return SkillResult(False, "¿Qué página o búsqueda quieres abrir?")
        return result_from_action(eng.open_url(url, confirmed=ctx.confirm))

    def _url_from_rag(self, ctx: SkillContext) -> str | None:
        try:
            from jarvis.config import get_config
            from jarvis.rag.factory import build_rag_stack

            cfg = get_config()
            if not cfg.rag.enabled:
                return None
            _, orch = build_rag_stack(cfg)
            cache = ctx.config.get("rag_session_cache")
            if isinstance(cache, dict):
                orch.session_cache = cache
            answer = orch.ask(ctx.user_text)
            if not answer.sufficient:
                # aún así buscar URL en fragmentos
                for c in answer.citations:
                    found = _extract_url_from_text(c.fragment)
                    if found:
                        return found
                return None
            found = _extract_url_from_text(answer.answer)
            if found:
                return found
            for c in answer.citations:
                found = _extract_url_from_text(c.fragment)
                if found:
                    return found
            # pedir al LLM solo la URL
            from jarvis.providers.base import ChatMessage

            reply = orch.llm.chat(
                [
                    ChatMessage(
                        role="system",
                        content=(
                            "Extrae solo la URL del contexto. "
                            "Si no hay URL, responde NONE."
                        ),
                    ),
                    ChatMessage(
                        role="user",
                        content=f"Pregunta: {ctx.user_text}\n\nRespuesta: {answer.answer}",
                    ),
                ]
            )
            text = reply.text.strip()
            if text.upper() == "NONE":
                return None
            return _extract_url_from_text(text) or (
                text if urlparse(text).scheme in {"http", "https"} else None
            )
        except Exception:  # noqa: BLE001
            return None
