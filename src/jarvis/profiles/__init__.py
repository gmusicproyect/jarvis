"""Perfiles de rendimiento: performance / balanced / lightweight."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from jarvis.gui.api.config_store import load_raw_config, save_config_updates

ProfileName = Literal["performance", "balanced", "lightweight"]

PROFILES: dict[str, dict[str, Any]] = {
    "performance": {
        "description": "Equipos potentes — modelos mayores, visión y memoria completa",
        "updates": {
            "app.performance_profile": "performance",
            "llm.model": "llama3.2:3b",
            "stt.model_size": "small",
            "memory.semantic_enabled": True,
            "memory.short_term_turns": 30,
            "rag.enabled": True,
            "rag.top_k": 8,
            "vision.enabled": True,
            "vision.use_vision_by_default": True,
            "vision.use_ocr_by_default": True,
            "automation.enabled": True,
            "metrics.log_system_usage": True,
        },
        "recommended_models": ["llama3.2:3b", "nomic-embed-text", "llava"],
    },
    "balanced": {
        "description": "Configuración recomendada para uso diario",
        "updates": {
            "app.performance_profile": "balanced",
            "llm.model": "llama3.2:3b",
            "stt.model_size": "small",
            "memory.semantic_enabled": True,
            "memory.short_term_turns": 20,
            "rag.enabled": True,
            "rag.top_k": 5,
            "vision.enabled": True,
            "vision.use_vision_by_default": True,
            "vision.use_ocr_by_default": True,
            "automation.enabled": True,
            "metrics.log_system_usage": True,
        },
        "recommended_models": ["llama3.2:3b", "nomic-embed-text", "llava"],
    },
    "lightweight": {
        "description": "Menor RAM — modelos pequeños y menos servicios",
        "updates": {
            "app.performance_profile": "lightweight",
            "llm.model": "llama3.2:1b",
            "stt.model_size": "base",
            "memory.semantic_enabled": False,
            "memory.short_term_turns": 10,
            "rag.enabled": True,
            "rag.top_k": 3,
            "vision.enabled": False,
            "vision.use_vision_by_default": False,
            "automation.enabled": True,
            "metrics.log_system_usage": False,
            "session.followup_seconds": 4.0,
        },
        "recommended_models": ["llama3.2:1b", "nomic-embed-text"],
    },
}


def list_profiles() -> list[tuple[str, str]]:
    return [(name, meta["description"]) for name, meta in PROFILES.items()]


def get_profile(name: str) -> dict[str, Any]:
    key = name.lower().strip()
    if key not in PROFILES:
        raise KeyError(f"Perfil desconocido: {name}. Usa: {', '.join(PROFILES)}")
    return deepcopy(PROFILES[key])


def current_profile_name() -> str:
    raw = load_raw_config()
    app = raw.get("app") if isinstance(raw.get("app"), dict) else {}
    return str(app.get("performance_profile") or "balanced")


def apply_profile(name: str) -> dict[str, Any]:
    """Aplica el perfil a config.yaml y devuelve metadatos."""
    profile = get_profile(name)
    save_config_updates(profile["updates"])
    return profile
