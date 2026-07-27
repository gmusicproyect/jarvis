"""Tests Fase 0 — config y health."""

from __future__ import annotations

from jarvis import __version__
from jarvis.__main__ import main
from jarvis.config import clear_config_cache, load_config, project_root
from jarvis.platform import PlatformName, detect_platform


def test_version_string() -> None:
    assert __version__


def test_project_root_has_config() -> None:
    root = project_root()
    assert (root / "config" / "config.yaml").exists()


def test_load_config_defaults() -> None:
    clear_config_cache()
    cfg = load_config()
    assert cfg.llm.provider == "ollama"
    assert cfg.tts.provider == "kokoro"
    assert cfg.tts.voice == "em_santa"
    assert cfg.wake.model == "hey_jarvis"


def test_cli_version(capsys: object) -> None:
    assert main(["--version"]) == 0


def test_cli_health() -> None:
    clear_config_cache()
    assert main(["--health"]) == 0


def test_cli_health_vision_reports_runtime_not_just_config(capsys) -> None:  # noqa: ANN001
    """P0-2: --health reporta on/degraded/off según sondas, no solo config.yaml."""
    clear_config_cache()
    assert main(["--health"]) == 0
    out = capsys.readouterr().out
    line = next(ln for ln in out.splitlines() if ln.strip().startswith("Vision:"))
    assert line.strip().startswith(("Vision: on (", "Vision: degraded (", "Vision: off ("))


def test_detect_platform() -> None:
    plat = detect_platform()
    assert plat in {
        PlatformName.MACOS,
        PlatformName.WINDOWS,
        PlatformName.LINUX,
        PlatformName.UNKNOWN,
    }
