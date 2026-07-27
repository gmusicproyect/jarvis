"""Helpers compartidos para skills de automatización."""

from __future__ import annotations

from jarvis.automation.engine import AutomationEngine
from jarvis.skills.base import SkillContext, SkillResult


def get_engine(ctx: SkillContext) -> AutomationEngine | None:
    eng = ctx.config.get("automation")
    return eng if isinstance(eng, AutomationEngine) else None


def result_from_action(action_result) -> SkillResult:  # noqa: ANN001
    data = dict(action_result.data)
    data["permission_level"] = int(action_result.level.value)
    data["elapsed_ms"] = action_result.elapsed_ms
    if action_result.data.get("needs_confirm") or (
        not action_result.success and "confirmación" in action_result.message.lower()
    ):
        data["needs_confirm"] = True
    return SkillResult(
        success=action_result.success,
        message=action_result.message,
        data=data,
        error=action_result.error,
    )


APP_MAP = {
    "spotify": "Spotify",
    "safari": "Safari",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "cursor": "Cursor",
    "terminal": "Terminal",
    "finder": "Finder",
    "notes": "Notes",
    "notas": "Notes",
    "mail": "Mail",
    "calendario": "Calendar",
    "calendar": "Calendar",
    "musica": "Music",
    "music": "Music",
    "vscode": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "openai": None,  # URL, no app
}
