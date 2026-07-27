"""Factories de providers según config.yaml."""

from __future__ import annotations

from jarvis.audio.stt.faster_whisper_stt import FasterWhisperSTT
from jarvis.audio.tts.kokoro_tts import KokoroTTS, SystemTTS
from jarvis.audio.wake.openwakeword_provider import OpenWakeWordProvider
from jarvis.config.loader import JarvisConfig
from jarvis.hardening.recovery import ResilientTTS, register_default_recoveries
from jarvis.llm.ollama import OllamaProvider
from jarvis.providers.base import LLMProvider, STTProvider, TTSProvider, WakeProvider


def build_wake(cfg: JarvisConfig) -> WakeProvider:
    if cfg.wake.provider == "openwakeword":
        return OpenWakeWordProvider(cfg.wake)
    raise ValueError(f"Wake provider no soportado: {cfg.wake.provider}")


def build_stt(cfg: JarvisConfig) -> STTProvider:
    if cfg.stt.provider == "faster_whisper":
        return FasterWhisperSTT(cfg.stt)
    raise ValueError(f"STT provider no soportado: {cfg.stt.provider}")


def build_tts(cfg: JarvisConfig) -> TTSProvider:
    register_default_recoveries(cfg)
    system = SystemTTS(cfg.tts)
    if cfg.tts.provider == "system":
        return system
    if cfg.tts.provider == "kokoro":
        try:
            primary = KokoroTTS(cfg.tts)
        except Exception as exc:  # noqa: BLE001 — mlx_audio ausente u otro fallo de carga
            from jarvis.utils.logging import get_logger

            get_logger("jarvis.tts").warning(
                "kokoro_unavailable_fallback_system", error=str(exc)
            )
            return system
        # ResilientTTS no es Protocol estricto pero cumple speak/stop
        return ResilientTTS(primary, fallbacks=[system])  # type: ignore[return-value]
    raise ValueError(
        f"TTS provider '{cfg.tts.provider}' aún no implementado. "
        "Usa kokoro o system."
    )


def build_llm(cfg: JarvisConfig) -> LLMProvider:
    if cfg.llm.provider == "ollama":
        return OllamaProvider(cfg.llm)
    raise ValueError(
        f"LLM provider '{cfg.llm.provider}' no activo. Usa ollama."
    )
