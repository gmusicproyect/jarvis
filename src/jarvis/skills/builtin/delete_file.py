"""Eliminar archivo — por defecto a la papelera (CONFIRM); permanente = RESTRICTED."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from jarvis.automation.base import PermissionLevel
from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._automation import get_engine, result_from_action
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill


class DeleteFileSkill(Skill):
    name: ClassVar[str] = "delete_file"
    description: ClassVar[str] = (
        "Envía un archivo a la papelera (confirmación). "
        "Borrado permanente solo si se pide explícitamente (restringido)."
    )
    aliases: ClassVar[list[str]] = [
        "borra el archivo",
        "elimina el archivo",
        "a la papelera",
        "delete file",
    ]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.CONFIRM

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text,
            [
                "borra el archivo",
                "elimina el archivo",
                "borra archivo",
                "papelera",
                "elimina permanentemente",
            ],
            boost=0.96,
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        eng = get_engine(ctx)
        m = re.search(
            r"(?:borra|elimina)(?:\s+el)?\s+archivo\s+(.+)$",
            ctx.user_text,
            re.I,
        )
        raw = m.group(1).strip(" .\"'") if m else None
        if not raw:
            return SkillResult(False, "¿Qué archivo debo eliminar?")
        path = Path(raw).expanduser()
        if not path.exists():
            return SkillResult(False, f"No existe {path}.")

        permanent = "permanent" in ctx.user_text.lower() or "definitiv" in ctx.user_text.lower()
        if eng is None:
            return SkillResult(False, "AutomationEngine no disponible.")

        if permanent:
            self.required_permissions = RiskLevel.RESTRICTED  # type: ignore[misc]

            def _perm():
                from jarvis.automation.base import ActionResult

                eng.files.delete_permanent(path)
                return ActionResult(
                    True,
                    f"Eliminé permanentemente {path.name}.",
                    "delete_permanent",
                    PermissionLevel.RESTRICTED,
                    data={"path": str(path)},
                )

            return result_from_action(
                eng.run(
                    "delete_permanent",
                    f"Eliminar permanentemente {path}",
                    PermissionLevel.RESTRICTED,
                    _perm,
                    confirmed=ctx.confirm,
                )
            )
        return result_from_action(eng.trash_file(path, confirmed=ctx.confirm))
