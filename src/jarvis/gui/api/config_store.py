"""Persistencia de cambios GUI → config.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from jarvis.config.loader import project_root
from jarvis.utils.logging import get_logger


def config_yaml_path() -> Path:
    return project_root() / "config" / "config.yaml"


def load_raw_config() -> dict[str, Any]:
    path = config_yaml_path()
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def _set_path(data: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur: dict[str, Any] = data
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def save_config_updates(updates: dict[str, Any]) -> Path:
    """Aplica claves dotted (p.ej. ``llm.model``) y escribe YAML."""
    log = get_logger("jarvis.gui.config")
    path = config_yaml_path()
    data = load_raw_config()
    for key, value in updates.items():
        _set_path(data, key, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            data,
            fh,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    log.info("config_saved", path=str(path), keys=list(updates.keys()))
    return path
