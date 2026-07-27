"""Orquestador RAG: recupera, cita y responde (sin inventar)."""

from __future__ import annotations

from collections.abc import Callable

from jarvis.providers.base import ChatMessage, LLMProvider
from jarvis.rag.base import Citation, RAGAnswer, Retriever
from jarvis.utils.logging import get_logger

# Caché simple de sesión: query normalizada → chunks
SessionCache = dict[str, list]


class RAGOrchestrator:
    name = "rag"

    def __init__(
        self,
        retriever: Retriever,
        llm: LLMProvider,
        *,
        top_k: int = 5,
        min_score: float = 0.25,
        refuse_if_insufficient: bool = True,
        user_name: str = "Juan",
        session_cache: SessionCache | None = None,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.top_k = top_k
        self.min_score = min_score
        self.refuse_if_insufficient = refuse_if_insufficient
        self.user_name = user_name
        self.session_cache = session_cache if session_cache is not None else {}
        self._log = get_logger("jarvis.rag.orch")

    def _cache_key(self, query: str) -> str:
        return " ".join(query.lower().split())

    def ask(self, question: str) -> RAGAnswer:
        key = self._cache_key(question)
        used_cache = False
        hits = self.session_cache.get(key)
        if hits is None:
            hits = self.retriever.retrieve(question, top_k=self.top_k)
            # guardar para reutilizar en la misma sesión
            self.session_cache[key] = hits
        else:
            used_cache = True

        filtered = [h for h in hits if h.score >= self.min_score]
        citations = [
            Citation(
                source=h.chunk.source,
                page=h.chunk.page,
                fragment=h.chunk.text[:280],
                score=round(h.score, 4),
            )
            for h in filtered
        ]

        if not filtered:
            msg = (
                "No encontré evidencia suficiente en tus documentos para responder "
                "con confianza. Prueba a indexar más archivos o reformular la pregunta."
            )
            self._log.info("rag_insufficient", query=question)
            return RAGAnswer(
                answer=msg,
                citations=[],
                sufficient=False,
                used_session_cache=used_cache,
            )

        context_blocks = []
        for i, h in enumerate(filtered, start=1):
            page = f", pág. {h.chunk.page}" if h.chunk.page else ""
            context_blocks.append(
                f"[{i}] Fuente: {h.chunk.source}{page}\n{h.chunk.text}"
            )
        context = "\n\n".join(context_blocks)

        system = (
            f"Eres Jarvis, asistente de {self.user_name}. "
            "Responde SOLO con la información del contexto documental. "
            "Si el contexto NO responde la pregunta, responde exactamente con la línea:\n"
            "INSUFICIENTE: <motivo breve>\n"
            "y nada más. "
            "Si sí puedes responder, incluye referencias [n] a las fuentes usadas. "
            "No inventes datos."
        )
        user = (
            f"Pregunta: {question}\n\n"
            f"Contexto documental:\n{context}\n\n"
            "Respuesta en español. Si no hay evidencia, usa el formato INSUFICIENTE."
        )
        reply = self.llm.chat(
            [
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=user),
            ]
        )

        answer = reply.text.strip()
        if answer.upper().startswith("INSUFICIENTE"):
            parts = answer.split(":", 1)
            detail = parts[1].strip() if len(parts) > 1 else ""
            if detail and detail.upper() != "INSUFICIENTE":
                msg = (
                    detail
                    if detail.lower().startswith("no ")
                    else (
                        "No encontré evidencia suficiente en tus documentos. "
                        + detail
                    )
                )
            else:
                msg = (
                    "No encontré evidencia suficiente en tus documentos "
                    "para responder con confianza."
                )
            self._log.info("rag_llm_refused", query=question)
            return RAGAnswer(
                answer=msg,
                citations=[],
                sufficient=False,
                used_session_cache=used_cache,
            )

        # Apéndice de citas legible
        cite_lines = []
        for i, c in enumerate(citations, start=1):
            page = f", pág. {c.page}" if c.page is not None else ""
            cite_lines.append(
                f"[{i}] {c.source}{page} (confianza≈{c.score:.2f})"
            )
        if cite_lines:
            answer = answer + "\n\nFuentes:\n" + "\n".join(cite_lines)

        self._log.info(
            "rag_answered",
            citations=len(citations),
            used_cache=used_cache,
        )
        return RAGAnswer(
            answer=answer,
            citations=citations,
            sufficient=True,
            used_session_cache=used_cache,
        )


def bind_session_cache(
    orch: RAGOrchestrator, getter: Callable[[], SessionCache]
) -> None:
    """Permite enlazar caché externa (memoria de sesión del orchestrator de voz)."""
    orch.session_cache = getter()
