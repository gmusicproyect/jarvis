"""Tipos compartidos del sistema de skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    SAFE = "safe"
    CONFIRM = "confirm"
    RESTRICTED = "restricted"


@dataclass
class SkillResult:
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class SkillContext:
    """Contexto inyectado por el Skill Manager / orchestrator."""

    user_text: str
    user_name: str = "Juan"
    memory: Any = None  # MemoryService | None
    confirm: bool = False  # True si el usuario ya confirmó
    config: dict[str, Any] = field(default_factory=dict)
