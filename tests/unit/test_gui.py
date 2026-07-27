"""Tests Fase 7 — controlador GUI y persistencia (sin Qt obligatorio)."""

from __future__ import annotations

from pathlib import Path

import yaml

from jarvis.gui.api.config_store import save_config_updates
from jarvis.gui.api.controller import JarvisGuiController
from jarvis.gui.api.models import ConfigForm
from jarvis.gui import run_gui


def test_controller_status() -> None:
    ctrl = JarvisGuiController()
    snap = ctrl.status()
    assert snap.user_name
    assert snap.llm
    assert snap.modules
    names = {m.name for m in snap.modules}
    assert "LLM" in names
    assert "Ollama" in names
    assert "RAG" in names


def test_controller_dashboard() -> None:
    ctrl = JarvisGuiController()
    data = ctrl.dashboard()
    assert isinstance(data.memory_notes, list)
    assert isinstance(data.indexed_docs, list)
    assert "cpu" in data.performance


def test_config_form_roundtrip(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    yaml_path = cfg_dir / "config.yaml"
    yaml_path.write_text(
        "llm:\n  model: llama3.2:3b\n  provider: ollama\n"
        "vision:\n  model: llava\n  provider: ollama\n  ocr_provider: tesseract\n"
        "tts:\n  voice: em_santa\n  speed: 1.0\n"
        "app:\n  language: es\n"
        "wake:\n  model: hey_jarvis\n  threshold: 0.45\n"
        "rag:\n  knowledge_dir: knowledge\n  chunk_size: 800\n"
        "  chunk_overlap: 120\n  top_k: 5\n"
        "automation:\n  browser_provider: system_open\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "jarvis.gui.api.config_store.config_yaml_path", lambda: yaml_path
    )
    save_config_updates({"llm.model": "llama3.2:1b", "rag.top_k": 7})
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert data["llm"]["model"] == "llama3.2:1b"
    assert data["rag"]["top_k"] == 7


def test_apply_config_form_uses_store(monkeypatch) -> None:  # noqa: ANN001
    saved: dict = {}

    def fake_save(updates: dict) -> Path:
        saved.update(updates)
        return Path("/tmp/x.yaml")

    monkeypatch.setattr(
        "jarvis.gui.api.controller.save_config_updates", fake_save
    )
    monkeypatch.setattr(
        "jarvis.gui.api.controller.clear_config_cache", lambda: None
    )
    ctrl = JarvisGuiController()
    form = ctrl.get_config_form()
    form.llm_model = "test-model"
    form.rag_top_k = 3
    msg = ctrl.apply_config_form(form)
    assert "guardad" in msg.lower()
    assert saved.get("llm.model") == "test-model"
    assert saved.get("rag.top_k") == 3


def test_phase8_placeholders() -> None:
    items = JarvisGuiController().placeholder_phase8()
    assert len(items) >= 5
    assert any("plugin" in i.lower() for i in items)


def test_run_gui_unknown_backend() -> None:
    try:
        run_gui("nope")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_run_gui_future_backend() -> None:
    try:
        run_gui("web")
        assert False, "expected NotImplementedError"
    except NotImplementedError:
        pass
