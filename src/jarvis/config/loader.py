"""Carga tipada de configuración desde config.yaml + .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def project_root() -> Path:
    """Raíz del repo (carpeta que contiene pyproject.toml / config/)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "config").exists():
            return parent
    return Path.cwd()


class AppConfig(BaseModel):
    name: str = "Jarvis"
    version: str = "1.0.0-rc.1"
    user_name: str = "Juan"
    language: str = "es"
    onboarding_completed: bool = False
    performance_profile: str = "balanced"


class PathsConfig(BaseModel):
    data_dir: str = "data"
    logs_dir: str = "data/logs"
    db_path: str = "data/db/jarvis.db"
    chroma_dir: str = "data/chroma"
    documents_dir: str = "data/documents"
    sounds_dir: str = "assets/sounds"
    activation_sound: str = "/System/Library/Sounds/Ping.aiff"
    knowledge_dir: str = "knowledge"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    json_logs: bool = Field(default=False, alias="json")
    file: str = "data/logs/jarvis.log"

    model_config = {"populate_by_name": True}


class LLMConfig(BaseModel):
    provider: Literal[
        "ollama", "openai", "claude", "gemini", "mistral", "deepseek", "n8n"
    ] = "ollama"
    model: str = "llama3.2:3b"
    base_url: str = "http://127.0.0.1:11434"
    temperature: float = 0.7
    timeout_s: float = 120.0
    system_prompt: str = (
        "Eres Jarvis, un asistente ejecutivo. Responde en español de forma concisa. "
        "Dirígete al usuario por su nombre: {user_name}."
    )


class WakeConfig(BaseModel):
    provider: str = "openwakeword"
    model: str = "hey_jarvis"
    threshold: float = 0.45
    sample_rate: int = 16000
    chunk_samples: int = 1280


class STTConfig(BaseModel):
    provider: str = "faster_whisper"
    model_size: Literal["tiny", "base", "small", "medium", "large"] = "small"
    language: str = "es"
    auto_detect_english: bool = True
    device: str = "cpu"
    compute_type: str = "int8"


class TTSConfig(BaseModel):
    provider: Literal[
        "kokoro", "piper", "openai", "elevenlabs", "azure", "system"
    ] = "kokoro"
    voice: str = "em_santa"
    lang_code: str = "e"
    model: str = "mlx-community/Kokoro-82M-bf16"
    speed: float = 1.0


class CaptureConfig(BaseModel):
    voice_threshold: int = 1000
    silence_max_s: float = 1.4
    wait_voice_s: float = 5.0
    max_utterance_s: float = 15.0


class SessionConfig(BaseModel):
    followup_enabled: bool = True
    followup_seconds: float = 6.0
    cancel_phrases: list[str] = Field(
        default_factory=lambda: [
            "cancela",
            "detente",
            "para",
            "silencio",
            "stop",
            "cancel",
        ]
    )
    clap_enabled: bool = True
    clap_threshold: int = 15000
    clap_window_s: float = 1.5
    clap_count: int = 2


class MetricsConfig(BaseModel):
    enabled: bool = True
    log_system_usage: bool = True


class MemoryConfig(BaseModel):
    enabled: bool = True
    short_term_turns: int = 20
    persistent_provider: str = "sqlite"
    semantic_provider: str = "chroma"
    semantic_enabled: bool = True
    embedding_model: str = "nomic-embed-text"
    embedding_base_url: str = "http://127.0.0.1:11434"
    db_path: str = "data/db/jarvis.db"
    chroma_dir: str = "data/chroma"
    top_k: int = 5


class RAGConfig(BaseModel):
    enabled: bool = True
    collection: str = "jarvis_docs"
    chroma_dir: str = "data/chroma_rag"
    index_db: str = "data/db/rag_index.db"
    embedding_model: str = "nomic-embed-text"
    embedding_base_url: str = "http://127.0.0.1:11434"
    knowledge_dir: str = "knowledge"
    watch_enabled: bool = False
    top_k: int = 5
    min_score: float = 0.35
    chunk_size: int = 800
    chunk_overlap: int = 120
    max_file_mb: float = 25.0
    parallel_workers: int = 4
    cache_embeddings: bool = True
    cite_required: bool = True
    refuse_if_insufficient: bool = True
    use_llamaindex_splitter: bool = True


class SkillsConfig(BaseModel):
    enabled: bool = True
    plugin_dir: str = "skills"
    min_score: float = 0.55
    use_llm_router: bool = True
    weather: dict[str, object] = Field(
        default_factory=lambda: {
            "provider": "open_meteo",
            "latitude": 9.93,
            "longitude": -84.08,
            "city": "San José",
        }
    )
    news: dict[str, object] = Field(
        default_factory=lambda: {
            "rss_url": "https://feeds.bbci.co.uk/mundo/rss.xml",
            "limit": 3,
        }
    )


class GUIConfig(BaseModel):
    enabled: bool = False
    backend: str = "qt"  # qt | web (futuro) | tauri (futuro)
    start_minimized: bool = False
    show_tray: bool = True


class SecurityConfig(BaseModel):
    confirm_destructive: bool = True
    allow_restricted: bool = False
    privacy_mode: bool = False


class AutomationConfig(BaseModel):
    enabled: bool = True
    browser_provider: str = "system_open"  # system_open | playwright
    browser_headless: bool = False
    audit_db: str = "data/db/automation_audit.db"
    shell_allowlist: list[str] = Field(
        default_factory=lambda: [
            "ls",
            "pwd",
            "echo",
            "date",
            "whoami",
            "uname",
            "df",
            "du",
            "cat",
            "head",
            "tail",
            "wc",
            "which",
            "brew",
            "git",
            "python3",
            "poetry",
            "ollama",
        ]
    )
    screenshots_dir: str = "data/screenshots"


class VisionConfig(BaseModel):
    enabled: bool = True
    provider: str = "ollama"  # ollama | openai | gemini | stub
    model: str = "llava"
    base_url: str = "http://127.0.0.1:11434"
    ocr_provider: str = "tesseract"  # tesseract | easyocr | stub
    ocr_languages: list[str] = Field(default_factory=lambda: ["spa", "eng"])
    captures_dir: str = "data/screenshots"
    history_enabled: bool = True
    history_db: str = "data/db/vision_history.db"
    use_ocr_by_default: bool = True
    use_vision_by_default: bool = True


class PersonalityConfig(BaseModel):
    style: str = "executive_butler"
    humor: str = "moderate"
    address_user_by_name: bool = True


class JarvisConfig(BaseModel):
    """Árbol completo de config.yaml."""

    app: AppConfig = Field(default_factory=AppConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    wake: WakeConfig = Field(default_factory=WakeConfig)
    stt: STTConfig = Field(default_factory=STTConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    gui: GUIConfig = Field(default_factory=GUIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    personality: PersonalityConfig = Field(default_factory=PersonalityConfig)


class EnvSettings(BaseSettings):
    """Secretos y overrides desde .env / entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jarvis_user_name: str | None = None
    jarvis_config_path: str | None = None
    jarvis_data_dir: str | None = None
    jarvis_log_level: str | None = None
    jarvis_log_json: bool | None = None

    ollama_base_url: str | None = None
    ollama_model: str | None = None

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    elevenlabs_api_key: str | None = None
    azure_speech_key: str | None = None
    azure_speech_region: str | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config YAML inválido: {path}")
    return data


def _apply_env_overrides(cfg: JarvisConfig, env: EnvSettings) -> JarvisConfig:
    """Fusiona .env sobre YAML (env gana en campos soportados)."""
    data = cfg.model_dump(by_alias=True)
    if env.jarvis_user_name:
        data["app"]["user_name"] = env.jarvis_user_name
    if env.jarvis_data_dir:
        data["paths"]["data_dir"] = env.jarvis_data_dir
    if env.jarvis_log_level:
        data["logging"]["level"] = env.jarvis_log_level
    if env.jarvis_log_json is not None:
        data["logging"]["json"] = env.jarvis_log_json
    if env.ollama_base_url:
        data["llm"]["base_url"] = env.ollama_base_url
    if env.ollama_model:
        data["llm"]["model"] = env.ollama_model
    return JarvisConfig.model_validate(data)


def load_config(config_path: Path | None = None) -> JarvisConfig:
    """Carga config.yaml + .env desde la raíz del proyecto."""
    root = project_root()
    env = EnvSettings(_env_file=root / ".env")  # type: ignore[call-arg]
    path = (
        Path(env.jarvis_config_path)
        if env.jarvis_config_path
        else config_path or (root / "config" / "config.yaml")
    )
    raw = _load_yaml(path)
    cfg = JarvisConfig.model_validate(raw)
    return _apply_env_overrides(cfg, env)


@lru_cache(maxsize=1)
def get_config() -> JarvisConfig:
    """Singleton de configuración para la app."""
    return load_config()


def clear_config_cache() -> None:
    """Útil en tests."""
    get_config.cache_clear()
