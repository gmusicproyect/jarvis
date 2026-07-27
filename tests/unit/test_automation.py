"""Tests Fase 5 — AutomationEngine, permisos, skills."""

from __future__ import annotations

from pathlib import Path

from jarvis.automation.audit import AutomationAudit
from jarvis.automation.base import ActionResult, PermissionLevel
from jarvis.automation.engine import AutomationEngine
from jarvis.automation.gate import PermissionGate
from jarvis.skills.base import SkillContext
from jarvis.skills.builtin.clipboard import ClipboardSkill
from jarvis.skills.builtin.open_application import OpenApplicationSkill
from jarvis.skills.builtin.screenshot import ScreenshotSkill
from jarvis.skills.manager import SkillManager


class FakeApps:
    name = "fake_apps"

    def __init__(self) -> None:
        self.opened: list[str] = []

    def open_app(self, app_name: str) -> None:
        self.opened.append(app_name)

    def close_app(self, app_name: str) -> None:
        return None

    def is_running(self, app_name: str) -> bool:
        return app_name in self.opened


class FakeBrowser:
    name = "fake_browser"

    def __init__(self) -> None:
        self.urls: list[str] = []

    def open_url(self, url: str) -> None:
        self.urls.append(url)

    def search_google(self, query: str) -> None:
        self.urls.append(f"https://www.google.com/search?q={query}")

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


class FakeFiles:
    name = "fake_files"

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.trashed: list[Path] = []

    def open_path(self, path: Path) -> None:
        return None

    def open_folder(self, path: Path) -> None:
        return None

    def find(self, name: str, root: Path | None = None) -> list[Path]:
        hit = self.tmp / name
        hit.write_text("demo", encoding="utf-8")
        return [hit]

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


class FakeClipboard:
    name = "fake_clip"

    def __init__(self) -> None:
        self.buf = ""

    def read(self) -> str:
        return self.buf

    def write(self, text: str) -> None:
        self.buf = text


class FakeWindows:
    name = "fake_win"

    def list_windows(self) -> list[str]:
        return ["Finder", "Code"]

    def focus(self, title_or_app: str) -> None:
        return None

    def minimize(self, title_or_app: str | None = None) -> None:
        return None


class FakeKeyboard:
    name = "fake_kb"

    def type_text(self, text: str) -> None:
        return None

    def hotkey(self, *keys: str) -> None:
        return None


class FakeMouse:
    name = "fake_mouse"

    def click(self, x: int, y: int, button: str = "left") -> None:
        return None

    def move(self, x: int, y: int) -> None:
        return None


class FakeShell:
    name = "fake_shell"

    def run(self, command: str, *, allowed: bool = False) -> tuple[int, str, str]:
        return 0, f"ok:{command}", ""


class FakeShot:
    name = "fake_shot"

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp

    def capture(self, path: Path | None = None) -> Path:
        out = path or (self.tmp / "shot.png")
        out.write_bytes(b"png")
        return out


def _engine(tmp_path: Path) -> AutomationEngine:
    apps = FakeApps()
    eng = AutomationEngine(
        apps=apps,
        browser=FakeBrowser(),
        files=FakeFiles(tmp_path),
        clipboard=FakeClipboard(),
        windows=FakeWindows(),
        keyboard=FakeKeyboard(),
        mouse=FakeMouse(),
        shell=FakeShell(),
        screenshot=FakeShot(tmp_path),
        gate=PermissionGate(allow_restricted=False, confirm_destructive=True),
        audit=AutomationAudit(tmp_path / "audit.db"),
        user_name="Juan",
    )
    eng._apps_ref = apps  # type: ignore[attr-defined]
    return eng


def test_open_app_safe(tmp_path: Path) -> None:
    eng = _engine(tmp_path)
    result = eng.open_application("Visual Studio Code")
    assert result.success
    assert "Visual Studio Code" in eng.apps.opened  # type: ignore[attr-defined]


def test_confirm_gate_for_trash(tmp_path: Path) -> None:
    eng = _engine(tmp_path)
    path = tmp_path / "x.txt"
    path.write_text("x", encoding="utf-8")
    blocked = eng.trash_file(path, confirmed=False)
    assert not blocked.success
    assert blocked.data.get("needs_confirm")
    ok = eng.confirm_pending()
    assert ok is not None and ok.success


def test_restricted_blocked(tmp_path: Path) -> None:
    eng = _engine(tmp_path)
    bad = eng.run_shell("rm -rf /tmp/demo", confirmed=True)
    assert not bad.success
    assert "restringida" in bad.message.lower() or "bloqueada" in bad.message.lower()


def test_clipboard_skill(tmp_path: Path) -> None:
    eng = _engine(tmp_path)
    skill = ClipboardSkill()
    ctx = SkillContext(
        user_text="Copia este texto al portapapeles: hola jarvis",
        config={"automation": eng},
    )
    assert skill.can_handle(ctx.user_text) >= 0.85
    result = skill.execute(ctx)
    assert result.success
    assert eng.clipboard.read() == "hola jarvis"


def test_screenshot_skill(tmp_path: Path) -> None:
    eng = _engine(tmp_path)
    skill = ScreenshotSkill()
    assert skill.can_handle("Haz una captura de pantalla") >= 0.9
    result = skill.execute(SkillContext(user_text="captura", config={"automation": eng}))
    assert result.success


def test_open_application_skill_score() -> None:
    skill = OpenApplicationSkill()
    assert skill.can_handle("Abre Visual Studio Code.") >= 0.9


def test_skill_manager_discovers_automation_skills() -> None:
    mgr = SkillManager()
    mgr.load_builtin()
    names = {s.name for s in mgr.skills}
    for required in (
        "open_application",
        "browser",
        "filesystem",
        "clipboard",
        "terminal",
        "screenshot",
        "window_manager",
    ):
        assert required in names


def test_cancel_flag(tmp_path: Path) -> None:
    cancel = [False]
    eng = _engine(tmp_path)
    eng.set_cancel_flag(cancel)
    # force pending confirm then cancel
    path = tmp_path / "y.txt"
    path.write_text("y", encoding="utf-8")
    eng.trash_file(path, confirmed=False)
    eng.cancel_pending()
    assert eng.confirm_pending() is None
