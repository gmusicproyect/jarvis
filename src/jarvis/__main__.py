"""Punto de entrada: ``python -m jarvis`` / ``poetry run jarvis``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jarvis import __version__
from jarvis.config import clear_config_cache, get_config, project_root
from jarvis.utils.logging import get_logger, setup_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="Jarvis — asistente de voz local-first",
    )
    parser.add_argument("--version", action="store_true", help="Muestra la versión")
    parser.add_argument(
        "--health",
        action="store_true",
        help="Comprueba config sin cargar modelos de voz",
    )
    parser.add_argument(
        "--once-text",
        metavar="TEXTO",
        help="Modo prueba: skills/memoria/LLM/TTS sin micrófono",
    )

    sub = parser.add_subparsers(dest="command")

    p_index = sub.add_parser("index", help="Indexa una carpeta o archivo (RAG)")
    p_index.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Ruta a indexar (default: knowledge/)",
    )
    p_index.add_argument(
        "--force",
        action="store_true",
        help="Reindexa aunque no haya cambios",
    )

    p_ask = sub.add_parser("ask", help="Pregunta sobre documentos indexados")
    p_ask.add_argument("question", help="Pregunta en lenguaje natural")

    p_watch = sub.add_parser(
        "watch", help="Observa knowledge/ y reindexa cambios (Ctrl+C sale)"
    )
    p_watch.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Carpeta a observar (default: knowledge/)",
    )

    p_gui = sub.add_parser("gui", help="Abre la interfaz gráfica (bandeja + panel)")
    p_gui.add_argument(
        "--backend",
        default=None,
        help="qt (default) | web/tauri (futuro)",
    )

    from jarvis.cli_phase8 import add_phase8_parsers
    from jarvis.cli_phase9 import add_phase9_parsers

    add_phase8_parsers(sub)
    add_phase9_parsers(sub)
    return parser


def run_healthcheck() -> int:
    """Health ligero: config + sondas reales de dependencias opcionales (visión)."""
    import shutil

    cfg = get_config()
    setup_logging(cfg)
    log = get_logger("jarvis.health")
    root = project_root()
    checks = {
        "project_root": root.exists(),
        "config_yaml": (root / "config" / "config.yaml").exists(),
        "llm_provider": cfg.llm.provider == "ollama",
        "tts_default": cfg.tts.voice == "em_santa",
    }

    vision_status = "off"
    vision_detail = "desactivada en config"
    if cfg.vision.enabled:
        model_ok = False
        ocr_ok = False
        missing: list[str] = []
        try:
            import httpx

            url = cfg.llm.base_url.rstrip("/")
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{url}/api/tags")
                resp.raise_for_status()
                names = {m.get("name", "") for m in resp.json().get("models", [])}
            target = cfg.vision.model
            model_ok = any(
                n == target or n.startswith(target + ":") or n.split(":")[0] == target
                for n in names
            )
        except Exception:  # noqa: BLE001
            missing.append(f"ollama/{cfg.vision.model}")
        else:
            if not model_ok:
                missing.append(f"modelo {cfg.vision.model}")

        ocr = cfg.vision.ocr_provider
        if ocr == "tesseract":
            ocr_ok = shutil.which("tesseract") is not None
            if not ocr_ok:
                missing.append("tesseract")
        elif ocr == "stub":
            ocr_ok = True
        else:
            ocr_ok = True  # easyocr u otros: no sondamos binario aquí

        if model_ok and ocr_ok:
            vision_status = "on"
            vision_detail = f"{cfg.vision.provider}/{cfg.vision.model}, ocr={ocr}"
        elif not missing:
            vision_status = "degraded"
            vision_detail = f"config on pero incompleto ({cfg.vision.provider}/{cfg.vision.model}, ocr={ocr})"
        else:
            vision_status = "degraded"
            vision_detail = (
                f"config on; faltan: {', '.join(missing)} "
                f"({cfg.vision.provider}/{cfg.vision.model}, ocr={ocr})"
            )
        checks["vision_runtime"] = vision_status == "on"
    else:
        checks["vision_runtime"] = True  # off explícito no es fallo

    log.info(
        "healthcheck",
        version=__version__,
        vision_status=vision_status,
        **checks,
    )
    print(f"Jarvis {__version__} OK — {cfg.app.user_name}")
    print(f"  LLM: {cfg.llm.provider}/{cfg.llm.model}")
    print(f"  TTS: {cfg.tts.provider}/{cfg.tts.voice}")
    print(f"  Wake: {cfg.wake.provider}/{cfg.wake.model}")
    print(f"  RAG: {'on' if cfg.rag.enabled else 'off'} (top_k={cfg.rag.top_k})")
    print(
        f"  Automation: {'on' if cfg.automation.enabled else 'off'} "
        f"({cfg.automation.browser_provider})"
    )
    print(f"  Vision: {vision_status} ({vision_detail})")
    print(f"  GUI: {'on' if cfg.gui.enabled else 'off'} ({cfg.gui.backend})")
    print(f"  Follow-up: {cfg.session.followup_seconds}s")
    # No fallar el proceso solo por visión degradada (sigue siendo usable);
    # sí fallar si faltan cimientos (root/config/llm/tts).
    core_ok = all(
        checks[k]
        for k in ("project_root", "config_yaml", "llm_provider", "tts_default")
    )
    return 0 if core_ok else 1


def run_index(path: str | None, *, force: bool) -> int:
    from jarvis.rag.factory import build_rag_stack

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    if not cfg.rag.enabled:
        print("RAG desactivado en config.yaml")
        return 1
    target = Path(path) if path else project_root() / cfg.rag.knowledge_dir
    indexer, _ = build_rag_stack(cfg)
    print(f"Indexando: {target}")
    stats = indexer.index_path(target, force=force)
    print(
        f"Listo. vistos={stats['files_seen']} indexados={stats['indexed']} "
        f"omitidos={stats['skipped_unchanged']} chunks={stats['chunks']}"
    )
    if stats["errors"]:
        print("Errores:")
        for err in stats["errors"]:
            print(f"  - {err}")
        return 1
    return 0


def run_ask(question: str) -> int:
    from jarvis.rag.factory import build_rag_stack

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    if not cfg.rag.enabled:
        print("RAG desactivado en config.yaml")
        return 1
    _, orch = build_rag_stack(cfg)
    answer = orch.ask(question)
    print(answer.answer)
    return 0 if answer.sufficient else 2


def run_watch(path: str | None) -> int:
    from jarvis.rag.factory import build_rag_stack
    from jarvis.rag.watcher import KnowledgeWatcher

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    folder = Path(path) if path else project_root() / cfg.rag.knowledge_dir
    indexer, _ = build_rag_stack(cfg)
    # indexación inicial
    indexer.index_path(folder)
    watcher = KnowledgeWatcher(folder, indexer)
    print(f"Observando {folder} (Ctrl+C para salir)")
    watcher.run_forever()
    return 0


def run_once_text(text: str) -> int:
    """E2E parcial sin wake: skills / memoria / LLM → TTS."""
    from jarvis.app.orchestrator import Orchestrator
    from jarvis.brain.hybrid_router import RouteTarget
    from jarvis.events import EventBus
    from jarvis.providers.base import ChatMessage
    from jarvis.skills.base import SkillContext

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    log = get_logger("jarvis.once")
    orch = Orchestrator(cfg, EventBus())
    decision = orch.hybrid.decide(text)

    if decision.target == RouteTarget.CANCEL:
        orch.skills.cancel_pending()
        if orch.automation is not None:
            orch.automation.cancel_pending()
        print("Jarvis: Acción cancelada.")
        return 0

    if decision.target == RouteTarget.CONFIRM:
        result = orch.skills.confirm_pending()
        if result is None and orch.automation is not None:
            ar = orch.automation.confirm_pending()
            if ar is not None:
                from jarvis.skills.base import SkillResult

                result = SkillResult(ar.success, ar.message, data=dict(ar.data))
        msg = (
            result.message
            if result
            else "No hay ninguna acción pendiente de confirmar."
        )
        print(f"Jarvis: {msg}")
        orch.tts.speak(msg)
        return 0

    if decision.target == RouteTarget.MEMORY and orch.memory is not None:
        mem_reply = orch.memory.handle_command(text)
        if mem_reply:
            print(f"Jarvis: {mem_reply}")
            orch.tts.speak(mem_reply)
            return 0

    if decision.target == RouteTarget.SKILL and decision.skill is not None:
        ctx = SkillContext(
            user_text=text,
            user_name=cfg.app.user_name,
            memory=orch.memory,
            config=orch._skill_config(),
        )
        result = orch.skills.execute(decision.skill, ctx)
        log.info("skill_once", skill=decision.skill.name, source=decision.source)
        print(f"Jarvis: {result.message}")
        orch.tts.speak(result.message)
        return 0

    system = cfg.llm.system_prompt.format(user_name=cfg.app.user_name)
    messages = [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=text),
    ]
    reply = orch.llm.chat(messages)
    print(f"Jarvis: {reply.text}")
    orch.tts.speak(reply.text)
    return 0


def run_loop() -> int:
    from jarvis.app.orchestrator import Orchestrator
    from jarvis.events import EventBus

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    log = get_logger("jarvis.main")
    log.info("starting_voice_loop", version=__version__)
    orch = Orchestrator(cfg, EventBus())
    try:
        orch.run()
    except KeyboardInterrupt:
        orch.stop()
        print("\nJarvis fuera de línea.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if args.health:
        return run_healthcheck()
    if args.once_text:
        return run_once_text(args.once_text)
    if args.command == "index":
        return run_index(args.path, force=args.force)
    if args.command == "ask":
        return run_ask(args.question)
    if args.command == "watch":
        return run_watch(args.path)
    if args.command == "gui":
        return run_gui(getattr(args, "backend", None))
    if args.command == "plugins":
        from jarvis.cli_phase8 import cmd_plugins

        return cmd_plugins(args)
    if args.command == "models":
        from jarvis.cli_phase8 import cmd_models

        return cmd_models(args)
    if args.command == "backup":
        from jarvis.cli_phase8 import cmd_backup

        return cmd_backup(args)
    if args.command == "autostart":
        from jarvis.cli_phase8 import cmd_autostart

        return cmd_autostart(args)
    if args.command == "doctor":
        from jarvis.cli_phase9 import cmd_doctor

        return cmd_doctor(args)
    if args.command == "profile":
        from jarvis.cli_phase9 import cmd_profile

        return cmd_profile(args)
    if args.command == "onboard":
        from jarvis.cli_phase9 import cmd_onboard

        return cmd_onboard(args)
    if args.command == "privacy":
        from jarvis.cli_phase9 import cmd_privacy

        return cmd_privacy(args)
    return run_loop()


def run_gui(backend: str | None = None) -> int:
    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    from jarvis.gui import run_gui as launch

    return launch(backend or cfg.gui.backend)


if __name__ == "__main__":
    sys.exit(main())
