"""Skill Manager — descubrimiento, enrutado y ejecución con métricas."""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import pkgutil
import time
from pathlib import Path
from types import ModuleType
from typing import Any

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.skill import Skill
from jarvis.utils.logging import get_logger


class SkillManager:
    def __init__(
        self,
        *,
        plugin_dirs: list[Path] | None = None,
        auto_confirm_safe: bool = True,
        allow_restricted: bool = False,
    ) -> None:
        self._log = get_logger("jarvis.skills")
        self._skills: dict[str, Skill] = {}
        self._plugin_dirs = plugin_dirs or []
        self._auto_confirm_safe = auto_confirm_safe
        self._allow_restricted = allow_restricted
        self._pending_confirm: tuple[Skill, SkillContext] | None = None

    @property
    def skills(self) -> list[Skill]:
        return list(self._skills.values())

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill
        self._log.info(
            "skill_registered",
            name=skill.name,
            risk=skill.required_permissions.value,
        )

    def load_builtin(self) -> None:
        import jarvis.skills.builtin as builtin_pkg

        self._load_from_package(builtin_pkg)

    def load_plugins(self) -> None:
        for directory in self._plugin_dirs:
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.py")):
                if path.name.startswith("_"):
                    continue
                self._load_plugin_file(path)

    def discover(self) -> None:
        self.load_builtin()
        self.load_plugins()

    def _load_from_package(self, package: ModuleType) -> None:
        prefix = package.__name__ + "."
        for mod in pkgutil.iter_modules(package.__path__, prefix):
            module = importlib.import_module(mod.name)
            self._register_module_skills(module)

    def _load_plugin_file(self, path: Path) -> None:
        spec = importlib.util.spec_from_file_location(
            f"jarvis_plugins.{path.stem}", path
        )
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._register_module_skills(module)
        self._log.info("plugin_loaded", path=str(path))

    def _register_module_skills(self, module: ModuleType) -> None:
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, Skill)
                and obj is not Skill
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                self.register(obj())

    def select(self, text: str, min_score: float = 0.55) -> Skill | None:
        best: Skill | None = None
        best_score = 0.0
        for skill in self._skills.values():
            score = skill.can_handle(text)
            if score > best_score:
                best_score = score
                best = skill
        if best is None or best_score < min_score:
            return None
        self._log.info(
            "skill_selected",
            skill=best.name,
            score=round(best_score, 3),
            text=text,
        )
        return best

    def execute(
        self,
        skill: Skill,
        ctx: SkillContext,
        *,
        force: bool = False,
        allow_restricted: bool = False,
    ) -> SkillResult:
        risk = skill.required_permissions
        allow_restricted = allow_restricted or self._allow_restricted
        if risk == RiskLevel.RESTRICTED and not allow_restricted:
            self._log.warning("restricted_blocked", skill=skill.name)
            return SkillResult(
                success=False,
                message=(
                    f"La acción '{skill.name}' está restringida. "
                    "Activa security.allow_restricted en config.yaml si es necesario."
                ),
                data={
                    "skill": skill.name,
                    "risk": risk.value,
                    "blocked": True,
                },
            )
        if (
            not force
            and risk in {RiskLevel.CONFIRM, RiskLevel.RESTRICTED}
            and not ctx.confirm
        ):
            self._pending_confirm = (skill, ctx)
            return SkillResult(
                success=False,
                message=(
                    f"La acción '{skill.name}' requiere confirmación. "
                    "Di 'confirma' para proceder o 'cancela' para abortar."
                ),
                data={"needs_confirm": True, "skill": skill.name, "risk": risk.value},
            )

        t0 = time.perf_counter()
        try:
            result = skill.execute(ctx)
            # Si el engine pidió confirmación internamente, registrar pending
            if result.data.get("needs_confirm") and not ctx.confirm:
                self._pending_confirm = (skill, ctx)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            self._log.info(
                "skill_executed",
                skill=skill.name,
                success=result.success,
                elapsed_ms=round(elapsed_ms, 2),
                risk=risk.value,
                error=result.error,
            )
            result.data.setdefault("elapsed_ms", round(elapsed_ms, 2))
            result.data.setdefault("skill", skill.name)
            result.data.setdefault("risk", risk.value)
            return result
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.perf_counter() - t0) * 1000
            self._log.exception(
                "skill_failed",
                skill=skill.name,
                elapsed_ms=round(elapsed_ms, 2),
                error=str(exc),
            )
            return SkillResult(
                success=False,
                message=f"Falló la habilidad {skill.name}.",
                error=str(exc),
                data={"elapsed_ms": round(elapsed_ms, 2), "skill": skill.name},
            )

    def confirm_pending(self) -> SkillResult | None:
        if not self._pending_confirm:
            return None
        skill, ctx = self._pending_confirm
        self._pending_confirm = None
        ctx.confirm = True
        return self.execute(
            skill, ctx, force=True, allow_restricted=self._allow_restricted
        )

    def cancel_pending(self) -> None:
        self._pending_confirm = None

    def catalog_for_llm(self) -> str:
        lines = []
        for s in self.skills:
            lines.append(
                f"- {s.name}: {s.description} (aliases: {', '.join(s.aliases) or '—'})"
            )
        return "\n".join(lines)

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)
