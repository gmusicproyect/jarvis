"""Manifest y tipos de plugins Jarvis."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    author: str = ""
    description: str = ""
    permissions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    compatibility: str = ">=0.1.0"
    entry: str = "skill.py"
    enabled: bool = True


@dataclass
class InstalledPlugin:
    manifest: PluginManifest
    path: Path
    enabled: bool = True
    errors: list[str] = field(default_factory=list)


def load_manifest(path: Path) -> PluginManifest:
    data: dict[str, Any]
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"manifest inválido: {path}")
    data = raw
    return PluginManifest.model_validate(data)


def write_default_manifest(path: Path, name: str) -> None:
    manifest = PluginManifest(
        name=name,
        description=f"Plugin {name}",
        skills=[name],
    )
    path.write_text(
        yaml.safe_dump(manifest.model_dump(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
