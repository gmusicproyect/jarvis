"""Modelos de datos para la GUI (sin dependencias Qt)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModuleStatus:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class StatusSnapshot:
    running: bool
    mic_enabled: bool
    wake_active: bool
    user_name: str
    llm: str
    vision: str
    ocr: str
    rag: str
    memory: str
    ollama: str
    tts: str
    automation: str
    cpu_percent: float | None = None
    ram_mb: float | None = None
    avg_latency_ms: float | None = None
    last_interaction: str = "—"
    modules: list[ModuleStatus] = field(default_factory=list)


@dataclass
class ConversationTurn:
    role: str  # user | jarvis | system | error
    text: str
    elapsed_ms: float | None = None
    skill: str | None = None
    sources: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class DashboardData:
    conversations: list[ConversationTurn] = field(default_factory=list)
    memory_notes: list[str] = field(default_factory=list)
    indexed_docs: list[str] = field(default_factory=list)
    top_skills: list[tuple[str, int]] = field(default_factory=list)
    automations: list[str] = field(default_factory=list)
    vision_history: list[str] = field(default_factory=list)
    audit_rows: list[str] = field(default_factory=list)
    performance: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigForm:
    """Campos editables desde la GUI."""

    llm_model: str = ""
    vision_model: str = ""
    vision_provider: str = ""
    ocr_provider: str = ""
    tts_voice: str = ""
    language: str = "es"
    wake_model: str = ""
    wake_threshold: float = 0.45
    knowledge_dir: str = "knowledge"
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 5
    llm_provider: str = "ollama"
    browser_provider: str = "system_open"
    volume: float = 1.0  # mapea a tts.speed como proxy de volumen/velocidad
