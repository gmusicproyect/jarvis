"""Recuperaciones concretas: TTS fallback, Ollama reconnect."""

from __future__ import annotations

import time

import httpx

from jarvis.config.loader import JarvisConfig
from jarvis.hardening.errors import FailureRecord, get_error_handler
from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.hardening.recovery")


class ResilientTTS:
    """TTS con cadena de fallback (kokoro → system)."""

    def __init__(self, primary, fallbacks: list | None = None) -> None:  # noqa: ANN001
        self.primary = primary
        self.fallbacks = fallbacks or []
        self.active = primary
        self.name = getattr(primary, "name", "tts")

    def speak(self, text: str) -> None:
        providers = [self.active, self.primary, *self.fallbacks]
        seen: set[int] = set()
        last_exc: Exception | None = None
        for provider in providers:
            if provider is None or id(provider) in seen:
                continue
            seen.add(id(provider))
            try:
                provider.speak(text)
                self.active = provider
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                _LOG.warning(
                    "tts_provider_failed",
                    provider=getattr(provider, "name", type(provider).__name__),
                    error=str(exc),
                )
        if last_exc:
            get_error_handler().handle("tts", last_exc)
            raise last_exc

    def stop(self) -> None:
        for provider in [self.active, self.primary, *self.fallbacks]:
            if provider is None:
                continue
            stop = getattr(provider, "stop", None)
            if callable(stop):
                try:
                    stop()
                except Exception:  # noqa: BLE001
                    pass


class OllamaHealth:
    """Comprueba y reintenta conexión a Ollama."""

    def __init__(self, base_url: str, *, retries: int = 3, delay_s: float = 1.5) -> None:
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.delay_s = delay_s

    def ping(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                r = client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    def ensure(self) -> FailureRecord | None:
        if self.ping():
            return None
        for attempt in range(1, self.retries + 1):
            _LOG.info("ollama_reconnect_attempt", attempt=attempt)
            time.sleep(self.delay_s)
            if self.ping():
                rec = FailureRecord(
                    module="ollama",
                    error="temporary_unreachable",
                    user_message="Ollama volvió a estar disponible.",
                    recovered=True,
                    recovery_action=f"reconnect_attempt_{attempt}",
                )
                return rec
        return get_error_handler().handle(
            "ollama",
            ConnectionError(f"Ollama no responde en {self.base_url}"),
            user_message=(
                "Ollama no está disponible. Puedo seguir con skills locales "
                "(apps, archivos, fecha, calculadora) mientras se reinicia."
            ),
        )


def register_default_recoveries(cfg: JarvisConfig) -> None:
    handler = get_error_handler()
    health = OllamaHealth(cfg.llm.base_url)

    def _ollama_rec(exc: Exception) -> FailureRecord:
        result = health.ensure()
        if result and result.recovered:
            return result
        return FailureRecord(
            module="ollama",
            error=str(exc),
            user_message=(
                "Ollama no responde. Comandos locales disponibles; "
                "revisa que el servicio esté en marcha."
            ),
            recovered=False,
            recovery_action="degrade_to_local_skills",
        )

    def _tts_rec(exc: Exception) -> FailureRecord:
        return FailureRecord(
            module="tts",
            error=str(exc),
            user_message="Cambiando a voz del sistema.",
            recovered=True,
            recovery_action="fallback_system_tts",
        )

    handler.register_recovery("ollama", _ollama_rec)
    handler.register_recovery("tts", _tts_rec)
