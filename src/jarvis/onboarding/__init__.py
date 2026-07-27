"""Asistente de primer inicio (onboarding)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from jarvis.backup.manager import BackupManager
from jarvis.config import clear_config_cache, get_config, project_root
from jarvis.gui.api.config_store import save_config_updates
from jarvis.profiles import apply_profile
from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.onboarding")

AskFn = Callable[[str], str]
SayFn = Callable[[str], None]


@dataclass
class OnboardingResult:
    completed: bool
    user_name: str = ""
    voice: str = ""
    knowledge_dir: str = ""
    profile: str = "balanced"
    steps: list[str] = field(default_factory=list)
    backup_path: str | None = None


def needs_onboarding() -> bool:
    cfg = get_config()
    return not bool(getattr(cfg.app, "onboarding_completed", False))


def mark_onboarding_done() -> None:
    save_config_updates({"app.onboarding_completed": True})
    clear_config_cache()


def run_onboarding(
    *,
    ask: AskFn | None = None,
    say: SayFn | None = None,
    non_interactive: bool = False,
    user_name: str | None = None,
    profile: str = "balanced",
    skip_backup: bool = False,
) -> OnboardingResult:
    """
    Flujo guiado. En CLI interactivo usa input(); en tests/GUI pasar ask/say
    o non_interactive=True con valores por defecto.
    """
    clear_config_cache()
    cfg = get_config()
    result = OnboardingResult(completed=False)

    def _say(msg: str) -> None:
        if say:
            say(msg)
        else:
            print(msg)

    def _ask(prompt: str, default: str = "") -> str:
        if ask:
            return ask(prompt) or default
        if non_interactive:
            return default
        raw = input(f"{prompt} [{default}]: ").strip()
        return raw or default

    _say("Hola, soy Jarvis. Vamos a configurarme.")
    result.steps.append("welcome")

    name = user_name or _ask(
        "¿Cómo te llamo?",
        default=cfg.app.user_name or "Usuario",
    )
    save_config_updates({"app.user_name": name})
    result.user_name = name
    result.steps.append("user_name")
    _say(f"Encantado, {name}.")

    # Micrófono
    _say("Comprobando micrófono…")
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        inputs = [d for d in devices if d.get("max_input_channels", 0) > 0]
        if inputs:
            _say(f"Micrófono OK ({len(inputs)} dispositivo(s)).")
            result.steps.append("microphone_ok")
        else:
            _say("No detecté micrófono. Podrás configurarlo después en Ajustes del Sistema.")
            result.steps.append("microphone_missing")
    except Exception:  # noqa: BLE001
        _say("No pude consultar el audio ahora. Continúo.")
        result.steps.append("microphone_skip")

    # Voz TTS
    voice = _ask(
        "Elige voz TTS (em_santa / system)",
        default=cfg.tts.voice or "em_santa",
    )
    if voice == "system":
        save_config_updates({"tts.provider": "system", "tts.voice": "system"})
    else:
        save_config_updates({"tts.provider": "kokoro", "tts.voice": voice})
    result.voice = voice
    result.steps.append("voice")

    # Perfil
    prof = _ask(
        "Perfil de rendimiento (performance / balanced / lightweight)",
        default=profile,
    )
    try:
        apply_profile(prof)
        result.profile = prof
        result.steps.append(f"profile:{prof}")
        _say(f"Perfil «{prof}» aplicado.")
    except KeyError:
        apply_profile("balanced")
        result.profile = "balanced"
        result.steps.append("profile:balanced")
        _say("Perfil balanced aplicado (valor por defecto).")

    # Knowledge
    knowledge = _ask(
        "Carpeta de conocimiento (RAG)",
        default=str(project_root() / cfg.rag.knowledge_dir),
    )
    kpath = Path(knowledge).expanduser()
    kpath.mkdir(parents=True, exist_ok=True)
    # Si es ruta absoluta fuera del repo, guardar relativa solo si está bajo root
    root = project_root()
    try:
        rel = kpath.resolve().relative_to(root)
        save_config_updates({"rag.knowledge_dir": str(rel), "paths.knowledge_dir": str(rel)})
    except ValueError:
        save_config_updates({"rag.knowledge_dir": str(kpath)})
    result.knowledge_dir = str(kpath)
    result.steps.append("knowledge")

    # Modelos recomendados (solo informar; pull es opcional)
    _say(
        "Modelos recomendados: llama3.2:3b, nomic-embed-text"
        + (" (y llava si usas visión)" if result.profile != "lightweight" else "")
        + ".\n  Descárgalos con: poetry run jarvis models pull <nombre>"
    )
    result.steps.append("models_hint")

    # Wake word hint
    _say(
        "Wake word: di «Hey Jarvis» cuando el micrófono esté activo. "
        "Prueba más tarde con: poetry run jarvis"
    )
    result.steps.append("wake_hint")

    # Backup inicial
    if not skip_backup:
        try:
            clear_config_cache()
            cfg2 = get_config()
            bm = BackupManager(cfg2)
            path = bm.create(label="onboarding")
            result.backup_path = str(path)
            result.steps.append("backup")
            _say(f"Backup inicial creado: {path}")
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("onboarding_backup_failed", error=str(exc))
            _say(f"No pude crear el backup inicial: {exc}")
            result.steps.append("backup_skip")

    mark_onboarding_done()
    result.completed = True
    result.steps.append("done")
    _say("Listo. Ya puedes usar Jarvis. Ejecuta «jarvis doctor» si quieres un diagnóstico.")
    _LOG.info("onboarding_completed", user=name, profile=result.profile)
    return result
