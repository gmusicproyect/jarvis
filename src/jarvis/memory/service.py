"""Servicio de memoria unificado + parsing de comandos en español."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from jarvis.memory.base import (
    MemoryItem,
    MemoryKind,
    PersistentMemory,
    SemanticMemory,
    SessionMemory,
)
from jarvis.utils.logging import get_logger


class MemoryAction(str, Enum):
    REMEMBER_NAME = "remember_name"
    REMEMBER_FACT = "remember_fact"
    SAVE_NOTE = "save_note"
    RECALL = "recall"
    LIST_NOTES = "list_notes"
    FORGET = "forget"
    NONE = "none"


@dataclass
class MemoryCommand:
    action: MemoryAction
    payload: str = ""


_RE_NAME = re.compile(
    r"(?:recuerda(?:\s+que)?|mi nombre es|ll[aá]mame)\s+(?:que\s+)?(?:me\s+llamo\s+|mi\s+nombre\s+es\s+)?(.+)$",
    re.I,
)
_RE_NOTE = re.compile(
    r"(?:guarda(?:\s+esta)?\s+nota|anota|apunta)(?:\s*:|\s+)\s*(.+)$",
    re.I,
)
_RE_REMEMBER = re.compile(
    r"(?:recuerda(?:\s+que)?|no olvides(?:\s+que)?)\s+(.+)$",
    re.I,
)
_RE_RECALL = re.compile(
    r"(?:qu[eé]\s+recuerdas\s+sobre|qu[eé]\s+sabes\s+de|recuerda(?:s)?\s+(?:algo\s+)?(?:sobre|de))\s+(.+)$",
    re.I,
)
_RE_LIST_NOTES = re.compile(
    r"(?:mu[eé]strame|lista|ense[nñ]ame)\s+(?:mis\s+)?notas",
    re.I,
)
_RE_FORGET = re.compile(
    r"(?:olvida|borra|elimina(?:\s+el\s+recuerdo)?(?:\s+de)?)\s+(.+)$",
    re.I,
)


def parse_memory_command(text: str) -> MemoryCommand:
    raw = text.strip()
    if not raw:
        return MemoryCommand(MemoryAction.NONE)

    if _RE_LIST_NOTES.search(raw):
        return MemoryCommand(MemoryAction.LIST_NOTES)

    m = _RE_FORGET.match(raw)
    if m:
        return MemoryCommand(MemoryAction.FORGET, m.group(1).strip(" ."))

    m = _RE_NOTE.match(raw)
    if m:
        return MemoryCommand(MemoryAction.SAVE_NOTE, m.group(1).strip(" ."))

    m = _RE_NAME.match(raw)
    if m and ("nombre" in raw.lower() or "llamo" in raw.lower() or "llámame" in raw.lower() or "llamame" in raw.lower()):
        name = m.group(1).strip(" .")
        name = re.sub(r"^(que\s+)?(mi\s+nombre\s+es\s+|me\s+llamo\s+)", "", name, flags=re.I)
        return MemoryCommand(MemoryAction.REMEMBER_NAME, name.strip(" ."))

    # "Recuerda que mi nombre es X"
    m2 = re.search(r"mi\s+nombre\s+es\s+([A-Za-zÁÉÍÓÚáéíóúñÑ ]+)$", raw, re.I)
    if m2 and re.search(r"recuerda|llam", raw, re.I):
        return MemoryCommand(MemoryAction.REMEMBER_NAME, m2.group(1).strip(" ."))

    m = _RE_RECALL.match(raw)
    if m:
        return MemoryCommand(MemoryAction.RECALL, m.group(1).strip(" .?"))

    m = _RE_REMEMBER.match(raw)
    if m:
        payload = m.group(1).strip(" .")
        if "nombre" in payload.lower():
            m3 = re.search(r"nombre\s+es\s+(.+)$", payload, re.I)
            if m3:
                return MemoryCommand(MemoryAction.REMEMBER_NAME, m3.group(1).strip(" ."))
        return MemoryCommand(MemoryAction.REMEMBER_FACT, payload)

    return MemoryCommand(MemoryAction.NONE)


class MemoryService:
    """Fachada: sesión + persistente + semántica."""

    def __init__(
        self,
        session: SessionMemory,
        persistent: PersistentMemory,
        semantic: SemanticMemory | None,
        *,
        top_k: int = 5,
        user_name: str = "Juan",
    ) -> None:
        self.session = session
        self.persistent = persistent
        self.semantic = semantic
        self.top_k = top_k
        self.user_name = user_name
        self._log = get_logger("jarvis.memory")
        # Sembrar nombre de config si no existe
        if not self.persistent.get_profile("name"):
            self.persistent.upsert_profile("name", user_name)

    def handle_command(self, text: str) -> str | None:
        """Si es comando de memoria, ejecuta y devuelve respuesta hablable."""
        from jarvis.privacy import is_full_forget_command

        if is_full_forget_command(text):
            return self.wipe_personal_data(keep_name=True)

        cmd = parse_memory_command(text)
        if cmd.action == MemoryAction.NONE:
            return None

        if cmd.action == MemoryAction.REMEMBER_NAME:
            self.persistent.upsert_profile("name", cmd.payload)
            self.user_name = cmd.payload
            item = self.persistent.add_item(
                MemoryKind.PROFILE, f"El nombre del usuario es {cmd.payload}", title="nombre"
            )
            self._index(item)
            return f"De acuerdo, recordaré que te llamas {cmd.payload}."

        if cmd.action == MemoryAction.SAVE_NOTE:
            item = self.persistent.add_item(MemoryKind.NOTE, cmd.payload, title="nota")
            self._index(item)
            return "Nota guardada."

        if cmd.action == MemoryAction.REMEMBER_FACT:
            item = self.persistent.add_item(MemoryKind.FACT, cmd.payload, title="hecho")
            self._index(item)
            return "Queda anotado en mi memoria."

        if cmd.action == MemoryAction.LIST_NOTES:
            notes = self.persistent.list_items(MemoryKind.NOTE)
            if not notes:
                return "No tienes notas guardadas todavía."
            body = "; ".join(n.content for n in notes[:8])
            return f"Tus notas: {body}"

        if cmd.action == MemoryAction.RECALL:
            return self.recall(cmd.payload)

        if cmd.action == MemoryAction.FORGET:
            prior = self.persistent.search_items(cmd.payload)
            if self.semantic:
                for item in prior:
                    self.semantic.delete(item.id)
            n = self.persistent.forget_matching(cmd.payload)
            return (
                f"He olvidado {n} recuerdo(s) relacionados con {cmd.payload}."
                if n
                else f"No encontré recuerdos sobre {cmd.payload}."
            )

        return None

    def wipe_personal_data(self, *, keep_name: bool = True) -> str:
        """Borra toda la memoria personal (comando de privacidad por voz)."""
        from jarvis.config import get_config
        from jarvis.privacy import wipe_all_memory

        cfg = get_config()
        stats = wipe_all_memory(cfg, keep_user_name=keep_name)
        self.session.clear()
        if keep_name and self.user_name:
            try:
                self.persistent.upsert_profile("name", self.user_name)
            except Exception:  # noqa: BLE001
                pass
        return (
            f"He eliminado toda tu memoria personal "
            f"({stats['sqlite_items']} recuerdos). "
            "Si quieres, puedo empezar de cero."
        )

    def recall(self, query: str) -> str:
        hits: list[MemoryItem] = []
        if self.semantic:
            hits.extend(self.semantic.retrieve(query, top_k=self.top_k))
        if not hits:
            hits.extend(self.persistent.search_items(query)[: self.top_k])
        profile = self.persistent.all_profile()
        parts: list[str] = []
        if profile:
            parts.append(
                "Perfil: " + ", ".join(f"{k}={v}" for k, v in profile.items())
            )
        if hits:
            parts.append(
                "Recuerdos: " + "; ".join(h.content for h in hits[: self.top_k])
            )
        if not parts:
            return f"No recuerdo nada específico sobre {query}."
        return " ".join(parts)

    def context_for_llm(self, user_text: str) -> str:
        """Bloque de contexto (perfil + semántica + hechos recientes)."""
        chunks: list[str] = []
        profile = self.persistent.all_profile()
        if profile:
            chunks.append(
                "Perfil del usuario: "
                + ", ".join(f"{k}={v}" for k, v in profile.items())
            )
        if self.semantic:
            for item in self.semantic.retrieve(user_text, top_k=self.top_k):
                chunks.append(f"- {item.content}")
        else:
            for item in self.persistent.search_items(user_text)[: self.top_k]:
                chunks.append(f"- {item.content}")
        return "\n".join(chunks)

    def _index(self, item: MemoryItem) -> None:
        if self.semantic:
            try:
                self.semantic.index(item)
            except Exception as exc:  # noqa: BLE001
                self._log.warning("semantic_index_failed", error=str(exc))
