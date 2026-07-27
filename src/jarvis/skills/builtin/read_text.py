"""Leer archivos de texto."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill


class ReadTextFileSkill(Skill):
    name: ClassVar[str] = "read_text_file"
    description: ClassVar[str] = "Lee el contenido de un archivo de texto"
    aliases: ClassVar[list[str]] = ["lee el archivo", "lee archivo", "abre y lee"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text, ["lee el archivo", "lee archivo", "lee el texto", "lee el fichero"], boost=0.9
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        m = re.search(
            r"(?:lee(?:r)?(?:\s+el)?\s+archivo)\s+(.+)$",
            ctx.user_text,
            re.I,
        )
        raw = m.group(1).strip(" .\"'") if m else None
        if not raw:
            m2 = re.search(r"(/[^\s]+|~\/[^\s]+|[\w\-./]+\.[\w]+)", ctx.user_text)
            raw = m2.group(1) if m2 else None
        if not raw:
            return SkillResult(False, "Indica la ruta del archivo.")
        path = Path(raw).expanduser()
        if not path.exists() or not path.is_file():
            return SkillResult(False, f"No existe el archivo {path}.")
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            return SkillResult(False, "No pude leer el archivo.", error=str(exc))
        snippet = text.strip()
        if len(snippet) > 800:
            snippet = snippet[:800] + "…"
        return SkillResult(
            True,
            f"Contenido de {path.name}: {snippet}",
            data={"path": str(path), "chars": len(text)},
        )
