"""Tests de factory / config Fase 1."""

from jarvis.config import clear_config_cache, load_config


def test_fase1_config_keys() -> None:
    clear_config_cache()
    cfg = load_config()
    assert cfg.session.followup_enabled is True
    assert "cancela" in cfg.session.cancel_phrases
    assert cfg.capture.silence_max_s > 0
    assert cfg.metrics.enabled is True
    assert cfg.llm.provider == "ollama"
    assert cfg.tts.voice == "em_santa"
    assert "{user_name}" in cfg.llm.system_prompt
