"""Tests Fase 8 — hardening, plugins, backup, secrets."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from jarvis.backup.manager import BackupManager
from jarvis.hardening.errors import ErrorHandler, get_error_handler
from jarvis.hardening.recovery import ResilientTTS
from jarvis.plugins.manager import PluginManager
from jarvis.plugins.manifest import PluginManifest, load_manifest
from jarvis.security.secrets import EnvSecretStore, SecretManager


def test_error_handler_recovery() -> None:
    h = ErrorHandler()

    def rec(exc: Exception):
        from jarvis.hardening.errors import FailureRecord

        return FailureRecord(
            module="tts",
            error=str(exc),
            user_message="ok",
            recovered=True,
            recovery_action="fallback",
        )

    h.register_recovery("tts", rec)
    r = h.handle("tts", RuntimeError("boom"))
    assert r.recovered
    assert r.recovery_action == "fallback"


def test_resilient_tts_fallback() -> None:
    class Bad:
        name = "bad"

        def speak(self, text: str) -> None:
            raise RuntimeError("fail")

        def stop(self) -> None:
            return None

    class Good:
        name = "good"

        def __init__(self) -> None:
            self.said = ""

        def speak(self, text: str) -> None:
            self.said = text

        def stop(self) -> None:
            return None

    good = Good()
    tts = ResilientTTS(Bad(), fallbacks=[good])
    tts.speak("hola")
    assert good.said == "hola"


def test_plugin_manifest_and_list(tmp_path: Path) -> None:
    root = tmp_path / "plugins"
    plug = root / "demo"
    plug.mkdir(parents=True)
    (plug / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "demo",
                "version": "1.2.0",
                "description": "Demo",
                "permissions": ["safe"],
                "skills": ["demo"],
                "entry": "skill.py",
            }
        ),
        encoding="utf-8",
    )
    (plug / "skill.py").write_text(
        '''
from typing import ClassVar
from jarvis.skills.skill import Skill
from jarvis.skills.base import RiskLevel, SkillContext, SkillResult

class DemoSkill(Skill):
    name: ClassVar[str] = "demo"
    description: ClassVar[str] = "demo"
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE
    def can_handle(self, text: str) -> float:
        return 1.0 if "demo" in text.lower() else 0.0
    def execute(self, ctx: SkillContext) -> SkillResult:
        return SkillResult(True, "demo-ok")
''',
        encoding="utf-8",
    )
    pm = PluginManager(root, state_path=tmp_path / "state.json")
    items = pm.list_installed()
    assert len(items) == 1
    assert items[0].manifest.name == "demo"
    skills = pm.load_skills()
    assert any(s.name == "demo" for s in skills)
    pm.disable("demo")
    assert not pm.list_installed()[0].enabled
    pm.enable("demo")
    assert pm.list_installed()[0].enabled


def test_plugin_install_copy(tmp_path: Path) -> None:
    src = tmp_path / "srcplug"
    src.mkdir()
    (src / "manifest.yaml").write_text(
        "name: copied\nversion: 0.1.0\npermissions: [safe]\nskills: [copied]\nentry: skill.py\n",
        encoding="utf-8",
    )
    (src / "skill.py").write_text("# empty\n", encoding="utf-8")
    dest_root = tmp_path / "plugins"
    pm = PluginManager(dest_root, state_path=tmp_path / "st.json")
    installed = pm.install(str(src))
    assert installed.manifest.name == "copied"
    assert (dest_root / "copied" / "manifest.yaml").exists()
    pm.remove("copied")
    assert not (dest_root / "copied").exists()


def test_load_manifest_echo() -> None:
    path = Path(__file__).resolve().parents[2] / "plugins" / "echo_plugin" / "manifest.yaml"
    if path.exists():
        m = load_manifest(path)
        assert m.name == "echo_plugin"
        assert "safe" in m.permissions


def test_backup_create_restore(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    root = tmp_path / "proj"
    (root / "config").mkdir(parents=True)
    (root / "data" / "db").mkdir(parents=True)
    (root / "knowledge").mkdir(parents=True)
    (root / "config" / "config.yaml").write_text("app:\n  name: Jarvis\n", encoding="utf-8")
    (root / "data" / "db" / "jarvis.db").write_bytes(b"sqlite")
    (root / "knowledge" / "a.md").write_text("# hi", encoding="utf-8")

    monkeypatch.setattr("jarvis.backup.manager.project_root", lambda: root)
    bm = BackupManager(backup_dir=tmp_path / "backups")
    z = bm.create(label="test")
    assert z.exists()
    # mutate and restore
    (root / "config" / "config.yaml").write_text("app:\n  name: CHANGED\n", encoding="utf-8")
    bm.restore(z, force=True)
    text = (root / "config" / "config.yaml").read_text(encoding="utf-8")
    assert "Jarvis" in text


def test_secret_manager_env() -> None:
    sm = SecretManager(store=EnvSecretStore())
    sm.set("test_key_jarvis", "secret-value")
    assert sm.get("test_key_jarvis") == "secret-value"
    sm.delete("test_key_jarvis")


def test_get_error_handler_singleton() -> None:
    a = get_error_handler()
    b = get_error_handler()
    assert a is b
