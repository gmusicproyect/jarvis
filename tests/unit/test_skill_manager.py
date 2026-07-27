"""Integración Skill Manager + plugins dinámicos."""

from __future__ import annotations

from pathlib import Path

from jarvis.config import project_root
from jarvis.skills.base import RiskLevel, SkillContext
from jarvis.skills.manager import SkillManager


def test_manager_discovers_builtins_and_plugins() -> None:
    mgr = SkillManager(plugin_dirs=[project_root() / "skills"])
    mgr.discover()
    names = {s.name for s in mgr.skills}
    assert "datetime" in names
    assert "open_app" in names
    assert "calculator" in names
    assert "echo_plugin" in names  # cargado desde skills/


def test_manager_selects_datetime() -> None:
    mgr = SkillManager(plugin_dirs=[])
    mgr.load_builtin()
    skill = mgr.select("¿Qué hora es?", min_score=0.5)
    assert skill is not None
    assert skill.name == "datetime"


def test_manager_confirm_flow(tmp_path: Path) -> None:
    from jarvis.automation.audit import AutomationAudit
    from jarvis.automation.engine import AutomationEngine
    from jarvis.automation.gate import PermissionGate

    class _Apps:
        name = "a"

        def open_app(self, app_name: str) -> None:
            return None

        def close_app(self, app_name: str) -> None:
            return None

        def is_running(self, app_name: str) -> bool:
            return False

    class _Files:
        name = "f"

        def __init__(self) -> None:
            self.trashed: list[Path] = []

        def open_path(self, path: Path) -> None:
            return None

        def open_folder(self, path: Path) -> None:
            return None

        def find(self, name: str, root: Path | None = None) -> list[Path]:
            return []

        def move(self, src: Path, dest: Path) -> Path:
            return dest

        def copy(self, src: Path, dest: Path) -> Path:
            return dest

        def rename(self, src: Path, new_name: str) -> Path:
            return src.with_name(new_name)

        def trash(self, path: Path) -> None:
            self.trashed.append(path)

        def delete_permanent(self, path: Path) -> None:
            path.unlink(missing_ok=True)

    class _Clip:
        name = "c"

        def read(self) -> str:
            return ""

        def write(self, text: str) -> None:
            return None

    class _Win:
        name = "w"

        def list_windows(self) -> list[str]:
            return []

        def focus(self, title_or_app: str) -> None:
            return None

        def minimize(self, title_or_app: str | None = None) -> None:
            return None

    class _Kb:
        name = "k"

        def type_text(self, text: str) -> None:
            return None

        def hotkey(self, *keys: str) -> None:
            return None

    class _Mouse:
        name = "m"

        def click(self, x: int, y: int, button: str = "left") -> None:
            return None

        def move(self, x: int, y: int) -> None:
            return None

    class _Shell:
        name = "s"

        def run(self, command: str, *, allowed: bool = False) -> tuple[int, str, str]:
            return 0, "", ""

    class _Shot:
        name = "sh"

        def capture(self, path: Path | None = None) -> Path:
            p = path or (tmp_path / "s.png")
            p.write_bytes(b"x")
            return p

    class _Browser:
        name = "b"

        def open_url(self, url: str) -> None:
            return None

        def search_google(self, query: str) -> None:
            return None

        def click(self, selector: str) -> None:
            return None

        def fill(self, selector: str, text: str) -> None:
            return None

        def get_page_text(self) -> str:
            return ""

        def extract_tables(self) -> list:
            return []

        def screenshot(self, path: Path) -> Path:
            return path

        def download(self, url: str, dest: Path) -> Path:
            return dest

        def close(self) -> None:
            return None

    files = _Files()
    eng = AutomationEngine(
        apps=_Apps(),
        browser=_Browser(),
        files=files,
        clipboard=_Clip(),
        windows=_Win(),
        keyboard=_Kb(),
        mouse=_Mouse(),
        shell=_Shell(),
        screenshot=_Shot(),
        gate=PermissionGate(allow_restricted=False, confirm_destructive=True),
        audit=AutomationAudit(tmp_path / "audit.db"),
    )
    mgr = SkillManager(plugin_dirs=[])
    mgr.load_builtin()
    skill = mgr.get("delete_file")
    assert skill is not None
    target = tmp_path / "x.txt"
    target.write_text("x", encoding="utf-8")
    ctx = SkillContext(
        user_text=f"Borra el archivo {target}",
        config={"automation": eng},
    )
    first = mgr.execute(skill, ctx)
    assert first.data.get("needs_confirm") is True
    assert target.exists()
    second = mgr.confirm_pending()
    assert second is not None
    assert second.success
    assert target in files.trashed


def test_add_skill_without_orchestrator_change(tmp_path: Path) -> None:
    """Nueva skill en directorio plugins → discover la carga."""
    plugin = tmp_path / "hola_skill.py"
    plugin.write_text(
        '''
from typing import ClassVar
from jarvis.skills.skill import Skill
from jarvis.skills.base import RiskLevel, SkillContext, SkillResult

class HolaSkill(Skill):
    name: ClassVar[str] = "hola_test"
    description: ClassVar[str] = "Dice hola"
    aliases: ClassVar[list[str]] = ["di hola test"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE
    def can_handle(self, text: str) -> float:
        return 1.0 if "hola test" in text.lower() else 0.0
    def execute(self, ctx: SkillContext) -> SkillResult:
        return SkillResult(True, "hola")
''',
        encoding="utf-8",
    )
    mgr = SkillManager(plugin_dirs=[tmp_path])
    mgr.load_plugins()
    assert mgr.get("hola_test") is not None
    r = mgr.execute(mgr.get("hola_test"), SkillContext(user_text="hola test"))  # type: ignore[arg-type]
    assert r.success
