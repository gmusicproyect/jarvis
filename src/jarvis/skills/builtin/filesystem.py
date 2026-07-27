"""Skill: sistema de archivos (buscar, abrir, papelera, renombrar)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from jarvis.automation.base import PermissionLevel
from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import norm, score_keywords
from jarvis.skills.skill import Skill


class FilesystemSkill(Skill):
    name: ClassVar[str] = "filesystem"
    description: ClassVar[str] = (
        "Busca, abre, mueve, renombra archivos o los envía a la papelera"
    )
    aliases: ClassVar[list[str]] = [
        "busca el archivo",
        "abre el archivo",
        "papelera",
        "renombra",
        "abre la carpeta",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        n = norm(text)
        keys = [
            "archivo",
            "carpeta",
            "xlsx",
            "pdf",
            "docx",
            "papelera",
            "renombra",
            "renombrar",
            "mueve",
            "copia",
            "presupuesto",
        ]
        if "busca" in n and any(k in n for k in ("archivo", ".xlsx", ".pdf", "documento")):
            return 0.95
        if "abre" in n and any(k in n for k in (".xlsx", ".pdf", ".docx", "carpeta", "archivo")):
            return 0.93
        return score_keywords(text, keys, boost=0.8)

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        if eng is None:
            return SkillResult(False, "AutomationEngine no disponible.")
        n = norm(ctx.user_text)

        if "papelera" in n or "a la basura" in n:
            self.required_permissions = RiskLevel.CONFIRM  # type: ignore[misc]
            path = self._extract_path(ctx.user_text)
            if not path:
                return SkillResult(False, "¿Qué archivo envío a la papelera?")
            return result_from_action(
                eng.trash_file(Path(path), confirmed=ctx.confirm)
            )

        if "renombr" in n:
            self.required_permissions = RiskLevel.CONFIRM  # type: ignore[misc]
            m = re.search(
                r"renombr\w+\s+(.+?)\s+(?:a|como)\s+(.+)$",
                ctx.user_text,
                re.I,
            )
            if not m:
                return SkillResult(False, "Indica: renombra X a Y")
            return result_from_action(
                eng.rename_file(
                    Path(m.group(1).strip().strip("\"'")),
                    m.group(2).strip().strip("\"'"),
                    confirmed=ctx.confirm,
                )
            )

        # buscar y abrir
        name = self._extract_filename(ctx.user_text)
        if not name:
            return SkillResult(False, "¿Qué archivo o carpeta busco?")
        if "carpeta" in n and "abre" in n:
            hits = eng.files.find(name)
            if not hits:
                return SkillResult(False, f"No encontré {name}.")
            folder = hits[0] if hits[0].is_dir() else hits[0].parent

            def _open():
                from jarvis.automation.base import ActionResult

                eng.files.open_folder(folder)
                return ActionResult(
                    True,
                    f"Abriendo carpeta {folder}.",
                    "open_folder",
                    PermissionLevel.SAFE,
                    data={"path": str(folder)},
                )

            return result_from_action(
                eng.run(
                    "open_folder",
                    f"Abrir carpeta {folder}",
                    PermissionLevel.SAFE,
                    _open,
                    confirmed=ctx.confirm,
                )
            )
        return result_from_action(eng.find_and_open(name))

    def _extract_filename(self, text: str) -> str | None:
        m = re.search(
            r"([\w.\-]+\.(?:xlsx|xls|pdf|docx?|pptx?|csv|txt|md|png|jpg))",
            text,
            re.I,
        )
        if m:
            return m.group(1)
        m = re.search(
            r"(?:archivo|documento|carpeta)\s+[«\"]?([\w.\-]+)[»\"]?",
            text,
            re.I,
        )
        return m.group(1) if m else None

    def _extract_path(self, text: str) -> str | None:
        m = re.search(r"(/[^\s]+|~/[^\s]+|[\w.\-]+\.\w+)", text)
        return m.group(1) if m else self._extract_filename(text)
