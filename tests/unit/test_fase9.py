"""Tests Fase 9 — release / doctor / profiles / privacy / onboarding."""

from __future__ import annotations

from pathlib import Path

import yaml

from jarvis.config.loader import JarvisConfig, clear_config_cache
from jarvis.doctor import format_report, run_doctor
from jarvis.onboarding import mark_onboarding_done, run_onboarding
from jarvis.privacy import (
    export_personal_data,
    is_full_forget_command,
    wipe_all_memory,
)
from jarvis.profiles import apply_profile, get_profile, list_profiles
from jarvis.release import PRODUCT_NAME, read_version_file


def test_version_file_and_product() -> None:
    assert PRODUCT_NAME == "Jarvis"
    ver = read_version_file()
    assert ver.startswith("1.0.0")


def test_profiles_defined() -> None:
    names = {n for n, _ in list_profiles()}
    assert names == {"performance", "balanced", "lightweight"}
    lite = get_profile("lightweight")
    assert lite["updates"]["vision.enabled"] is False
    assert lite["updates"]["stt.model_size"] == "base"


def test_apply_profile(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    cfg_path = cfg_dir / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"app": {"user_name": "Test", "performance_profile": "balanced"}}),
        encoding="utf-8",
    )
    import jarvis.gui.api.config_store as store

    monkeypatch.setattr(store, "project_root", lambda: tmp_path)
    apply_profile("lightweight")
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert data["app"]["performance_profile"] == "lightweight"
    assert data["vision"]["enabled"] is False


def test_forget_command_detection() -> None:
    assert is_full_forget_command("Jarvis, elimina todo lo que recuerdas de mí.")
    assert is_full_forget_command("borra toda mi memoria")
    assert not is_full_forget_command("olvida mi cita del martes")


def test_privacy_export_wipe(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    import jarvis.privacy as privacy

    monkeypatch.setattr(privacy, "project_root", lambda: tmp_path)

    db = tmp_path / "data" / "db"
    db.mkdir(parents=True)
    db_path = db / "jarvis.db"
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE profile (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
        CREATE TABLE memory_items (
          id TEXT PRIMARY KEY, kind TEXT, title TEXT, content TEXT, created_at TEXT
        );
        INSERT INTO profile VALUES ('name', 'Ana', '2026-01-01');
        INSERT INTO memory_items VALUES ('1', 'fact', 'x', 'le gusta el cafe', '2026-01-01');
        """
    )
    conn.commit()
    conn.close()

    cfg = JarvisConfig.model_validate(
        {"memory": {"db_path": "data/db/jarvis.db", "chroma_dir": "data/chroma"}}
    )
    out = export_personal_data(cfg, tmp_path / "export.json")
    assert out.exists()
    assert "le gusta el cafe" in out.read_text(encoding="utf-8")

    stats = wipe_all_memory(cfg, keep_user_name=True)
    assert stats["sqlite_items"] == 1
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0]
    name = conn.execute("SELECT value FROM profile WHERE key='name'").fetchone()
    conn.close()
    assert n == 0
    assert name is not None and name[0] == "Ana"


def test_doctor_runs() -> None:
    clear_config_cache()
    report = run_doctor(JarvisConfig())
    assert report.product == "Jarvis"
    assert any(c.name == "Python" for c in report.checks)
    text = format_report(report)
    assert "Python" in text


def test_onboarding_non_interactive(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    import jarvis.onboarding as ob
    import jarvis.gui.api.config_store as store
    import jarvis.config.loader as loader

    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "config.yaml").write_text(
        "app:\n  user_name: Temp\n  onboarding_completed: false\n"
        "rag:\n  knowledge_dir: knowledge\n"
        "tts:\n  voice: em_santa\n",
        encoding="utf-8",
    )
    (tmp_path / "knowledge").mkdir()

    monkeypatch.setattr(ob, "project_root", lambda: tmp_path)
    monkeypatch.setattr(store, "project_root", lambda: tmp_path)
    monkeypatch.setattr(loader, "project_root", lambda: tmp_path)

    clear_config_cache()

    def _fake_get_config() -> JarvisConfig:
        raw = yaml.safe_load((tmp_path / "config" / "config.yaml").read_text(encoding="utf-8"))
        return JarvisConfig.model_validate(raw or {})

    monkeypatch.setattr(ob, "get_config", _fake_get_config)
    monkeypatch.setattr(ob, "clear_config_cache", lambda: None)
    monkeypatch.setattr(loader, "get_config", _fake_get_config)
    monkeypatch.setattr(loader, "clear_config_cache", lambda: None)

    result = run_onboarding(
        non_interactive=True,
        user_name="RCUser",
        profile="balanced",
        skip_backup=True,
    )
    assert result.completed
    assert result.user_name == "RCUser"
    data = yaml.safe_load((tmp_path / "config" / "config.yaml").read_text(encoding="utf-8"))
    assert data["app"]["user_name"] == "RCUser"
    assert data["app"]["onboarding_completed"] is True


def test_mark_onboarding_done(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    import jarvis.gui.api.config_store as store
    import jarvis.onboarding as ob

    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "config.yaml").write_text("app: {}\n", encoding="utf-8")
    monkeypatch.setattr(store, "project_root", lambda: tmp_path)
    monkeypatch.setattr(ob, "clear_config_cache", lambda: None)
    mark_onboarding_done()
    data = yaml.safe_load((tmp_path / "config" / "config.yaml").read_text(encoding="utf-8"))
    assert data["app"]["onboarding_completed"] is True
