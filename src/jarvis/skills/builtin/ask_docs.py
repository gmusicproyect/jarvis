"""Skill: preguntas sobre documentos indexados (RAG)."""

from __future__ import annotations

from typing import ClassVar

from jarvis.rag.factory import build_rag_stack
from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill


class AskDocsSkill(Skill):
    name: ClassVar[str] = "ask_docs"
    description: ClassVar[str] = (
        "Responde preguntas usando documentos indexados (RAG) con citas"
    )
    aliases: ClassVar[list[str]] = [
        "qué dice el",
        "que dice el",
        "busca en documentos",
        "según el manual",
        "resume el",
        "dónde aparece",
        "que documentos",
        "contrato",
        "manual",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        keys = [
            "documento",
            "manual",
            "contrato",
            "pdf",
            "según el",
            "que dice",
            "qué dice",
            "resume el",
            "donde aparece",
            "dónde aparece",
            "busca en mis",
            "en el archivo",
            "kubernetes",
            "impuestos",
            "instalacion",
            "instalación",
        ]
        score = score_keywords(text, keys, boost=0.82)
        # preguntas "qué/dónde" + tema documental
        low = text.lower()
        if any(w in low for w in ("manual", "contrato", "documento", "pdf", "código", "codigo")):
            if any(w in low for w in ("qué", "que", "dónde", "donde", "busca", "resume")):
                score = max(score, 0.9)
        return score

    def execute(self, ctx: SkillContext) -> SkillResult:
        from jarvis.config import get_config

        cfg = get_config()
        if not cfg.rag.enabled:
            return SkillResult(False, "El módulo RAG está desactivado en config.yaml.")
        try:
            _indexer, orch = build_rag_stack(cfg)
            # reutilizar caché de sesión si el ctx la trae
            cache = ctx.config.get("rag_session_cache")
            if isinstance(cache, dict):
                orch.session_cache = cache
            answer = orch.ask(ctx.user_text)
            return SkillResult(
                answer.sufficient,
                answer.answer,
                data={
                    "citations": [
                        {
                            "source": c.source,
                            "page": c.page,
                            "score": c.score,
                        }
                        for c in answer.citations
                    ],
                    "used_session_cache": answer.used_session_cache,
                },
            )
        except Exception as exc:  # noqa: BLE001
            return SkillResult(False, "No pude consultar los documentos.", error=str(exc))
