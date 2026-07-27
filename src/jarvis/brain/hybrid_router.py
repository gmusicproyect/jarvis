"""Router híbrido: reglas rápidas + LLM cuando hay ambigüedad."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum

from jarvis.brain.intent import Intent, IntentKind, IntentRouter
from jarvis.memory.service import MemoryAction, parse_memory_command
from jarvis.providers.base import ChatMessage, LLMProvider
from jarvis.skills.manager import SkillManager
from jarvis.skills.skill import Skill
from jarvis.utils.logging import get_logger


class RouteTarget(str, Enum):
    CANCEL = "cancel"
    MEMORY = "memory"
    SKILL = "skill"
    CHAT = "chat"
    CONFIRM = "confirm"
    EMPTY = "empty"


@dataclass
class RouteDecision:
    target: RouteTarget
    text: str
    skill: Skill | None = None
    source: str = "rules"  # rules | llm
    score: float = 0.0


class HybridRouter:
    """Combina reglas, SkillManager y clasificación LLM (opaca al usuario)."""

    def __init__(
        self,
        cancel_router: IntentRouter,
        skills: SkillManager,
        llm: LLMProvider | None = None,
        *,
        llm_threshold: float = 0.55,
        ambiguous_band: float = 0.2,
    ) -> None:
        self._cancel = cancel_router
        self._skills = skills
        self._llm = llm
        self._llm_threshold = llm_threshold
        self._band = ambiguous_band
        self._log = get_logger("jarvis.router")

    def decide(self, text: str) -> RouteDecision:
        cleaned = text.strip()
        if not cleaned:
            return RouteDecision(RouteTarget.EMPTY, cleaned, source="rules")

        # Confirmación pendiente
        low = cleaned.lower()
        if low in {"confirma", "confirmo", "sí", "si", "dale", "ok", "okay"}:
            return RouteDecision(RouteTarget.CONFIRM, cleaned, source="rules", score=1.0)

        base: Intent = self._cancel.route(cleaned)
        if base.kind == IntentKind.CANCEL:
            return RouteDecision(RouteTarget.CANCEL, cleaned, source="rules", score=1.0)
        if base.kind == IntentKind.EMPTY:
            return RouteDecision(RouteTarget.EMPTY, cleaned, source="rules")

        mem = parse_memory_command(cleaned)
        if mem.action != MemoryAction.NONE:
            return RouteDecision(RouteTarget.MEMORY, cleaned, source="rules", score=0.99)

        from jarvis.privacy import is_full_forget_command

        if is_full_forget_command(cleaned):
            return RouteDecision(RouteTarget.MEMORY, cleaned, source="rules", score=1.0)

        # Scores de todas las skills
        scored: list[tuple[Skill, float]] = []
        for skill in self._skills.skills:
            scored.append((skill, skill.can_handle(cleaned)))
        scored.sort(key=lambda x: x[1], reverse=True)
        best_skill, best_score = scored[0] if scored else (None, 0.0)
        second = scored[1][1] if len(scored) > 1 else 0.0

        ambiguous = (
            best_skill is not None
            and best_score >= 0.4
            and (best_score - second) < self._band
            and best_score < 0.85
        )

        if best_skill and best_score >= self._llm_threshold and not ambiguous:
            return RouteDecision(
                RouteTarget.SKILL,
                cleaned,
                skill=best_skill,
                source="rules",
                score=best_score,
            )

        # LLM desempate / clasificación
        if self._llm is not None and (ambiguous or best_score < self._llm_threshold):
            llm_skill = self._classify_with_llm(cleaned)
            if llm_skill is not None:
                return RouteDecision(
                    RouteTarget.SKILL,
                    cleaned,
                    skill=llm_skill,
                    source="llm",
                    score=0.8,
                )

        if best_skill and best_score >= 0.45:
            return RouteDecision(
                RouteTarget.SKILL,
                cleaned,
                skill=best_skill,
                source="rules",
                score=best_score,
            )

        return RouteDecision(RouteTarget.CHAT, cleaned, source="rules", score=0.0)

    def _classify_with_llm(self, text: str) -> Skill | None:
        assert self._llm is not None
        catalog = self._skills.catalog_for_llm()
        prompt = (
            "Clasifica el pedido del usuario en UNA skill de la lista, "
            "o responde chat si ninguna aplica.\n"
            f"Skills:\n{catalog}\n\n"
            f'Usuario: "{text}"\n'
            'Responde JSON estricto: {"skill":"nombre"|null,"reason":"..."}'
        )
        try:
            resp = self._llm.chat(
                [
                    ChatMessage(role="system", content="Eres un clasificador de intenciones."),
                    ChatMessage(role="user", content=prompt),
                ]
            )
            raw = resp.text.strip()
            m = re.search(r"\{.*\}", raw, re.S)
            if not m:
                return None
            data = json.loads(m.group(0))
            name = data.get("skill")
            if not name or name == "null":
                return None
            skill = self._skills.get(str(name))
            self._log.info("llm_route", skill=name, reason=data.get("reason"))
            return skill
        except Exception as exc:  # noqa: BLE001
            self._log.warning("llm_route_failed", error=str(exc))
            return None
