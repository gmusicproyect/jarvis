"""Buscar archivos en el sistema."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import norm, score_keywords
from jarvis.skills.skill import Skill


class SearchFilesSkill(Skill):
    name: ClassVar[str] = "search_files"
    description: ClassVar[str] = "Busca archivos por nombre en el home del usuario"
    aliases: ClassVar[list[str]] = ["busca el archivo", "encuentra el archivo", "busca archivo"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        n = norm(text)
        # Si también pide abrir, filesystem gana
        if "abre" in n or "abrir" in n:
            return 0.55
        if "archivo" in n or ".pdf" in n or ".txt" in n or ".docx" in n or ".xlsx" in n:
            if any(w in n for w in ("busca", "encuentra", "localiza", "donde esta")):
                return 0.9
        return score_keywords(text, ["busca archivo", "encuentra archivo"], boost=0.75)

    def execute(self, ctx: SkillContext) -> SkillResult:
        m = re.search(
            r"(?:archivo|file)\s+([^\s]+)|busca(?:r)?\s+(?:el\s+)?(?:archivo\s+)?([^\s]+)",
            ctx.user_text,
            re.I,
        )
        query = None
        if m:
            query = m.group(1) or m.group(2)
        if not query:
            # última palabra con extensión
            m2 = re.search(r"([\w\-]+\.[\w]+)", ctx.user_text)
            query = m2.group(1) if m2 else None
        if not query:
            return SkillResult(False, "¿Qué archivo busco?")

        home = Path.home()
        # mdfind en macOS es rápido
        try:
            proc = subprocess.run(
                ["mdfind", "-onlyin", str(home), f"kMDItemFSName == '{query}'c"],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
            paths = [p for p in proc.stdout.splitlines() if p.strip()]
        except Exception:
            paths = list(home.rglob(query))[:10]  # fallback lento

        if not paths:
            return SkillResult(False, f"No encontré {query}.")
        top = paths[:5]
        msg = f"Encontré {len(paths)} resultado(s). El primero es {top[0]}."
        return SkillResult(True, msg, data={"paths": top, "count": len(paths)})
