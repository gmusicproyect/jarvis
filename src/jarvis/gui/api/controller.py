"""Controlador GUI — única puerta de la interfaz al núcleo."""

from __future__ import annotations

import sqlite3
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Callable

import httpx

from jarvis.config import clear_config_cache, get_config, project_root
from jarvis.gui.api.config_store import save_config_updates
from jarvis.gui.api.models import (
    ConfigForm,
    ConversationTurn,
    DashboardData,
    ModuleStatus,
    StatusSnapshot,
)
from jarvis.utils.logging import get_logger, setup_logging

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]


NotifyFn = Callable[[str, str, str], None]


class JarvisGuiController:
    """Servicio dedicado: la GUI solo habla con esta clase."""

    def __init__(self) -> None:
        self._log = get_logger("jarvis.gui.controller")
        self._running = False
        self._mic_enabled = True
        self._wake_active = True
        self._voice_thread: threading.Thread | None = None
        self._orch = None
        self._stop_flag = False
        self._conversation: list[ConversationTurn] = []
        self._latencies: list[float] = []
        self._skill_counter: Counter[str] = Counter()
        self._last_interaction = "—"
        self._notify: NotifyFn | None = None
        self._listeners: list[Callable[[StatusSnapshot], None]] = []
        clear_config_cache()
        self.cfg = get_config()
        setup_logging(self.cfg)

    def set_notifier(self, fn: NotifyFn) -> None:
        self._notify = fn

    def on_status(self, fn: Callable[[StatusSnapshot], None]) -> None:
        self._listeners.append(fn)

    def _emit_status(self) -> None:
        snap = self.status()
        for fn in list(self._listeners):
            try:
                fn(snap)
            except Exception:  # noqa: BLE001
                pass

    def notify(self, title: str, message: str, *, level: str = "info") -> None:
        if self._notify:
            self._notify(title, message, level)
        self._log.info("gui_notify", title=title, message=message, level=level)

    # --- lifecycle ---

    def start_voice(self) -> str:
        if self._running:
            return "Jarvis ya está en marcha."
        self._stop_flag = False
        self._running = True
        self._wake_active = True

        def _loop() -> None:
            try:
                from jarvis.app.orchestrator import Orchestrator
                from jarvis.events import EventBus

                clear_config_cache()
                cfg = get_config()
                bus = EventBus()
                orch = Orchestrator(cfg, bus)
                self._orch = orch
                # Enlazar eventos a conversación
                bus.subscribe(
                    "speech_recognized",
                    lambda text="", **_: self._on_user(text),
                )
                bus.subscribe(
                    "llm_response_ready",
                    lambda text="", model="", **kw: self._on_jarvis(
                        text, skill=model if str(model).startswith("skill:") else None
                    ),
                )
                bus.subscribe(
                    "error",
                    lambda message="", **_: self.notify(
                        "Error", str(message), level="error"
                    ),
                )
                self.notify("Jarvis", "Asistente de voz iniciado.", level="info")
                orch.run()
            except Exception as exc:  # noqa: BLE001
                self._log.exception("voice_loop_failed", error=str(exc))
                self.notify("Jarvis", f"Error en el loop de voz: {exc}", level="error")
            finally:
                self._running = False
                self._orch = None
                self._emit_status()

        self._voice_thread = threading.Thread(target=_loop, name="jarvis-voice", daemon=True)
        self._voice_thread.start()
        self._emit_status()
        return "Iniciando Jarvis…"

    def stop_voice(self) -> str:
        if self._orch is not None:
            try:
                self._orch.stop()
            except Exception:  # noqa: BLE001
                pass
        self._running = False
        self._wake_active = False
        self.notify("Jarvis", "Asistente detenido.", level="info")
        self._emit_status()
        return "Jarvis detenido."

    def set_mic_enabled(self, enabled: bool) -> None:
        self._mic_enabled = enabled
        self._wake_active = enabled and self._running
        self.notify(
            "Micrófono",
            "Activado" if enabled else "Silenciado",
            level="info",
        )
        self._emit_status()

    # --- conversation ---

    def _on_user(self, text: str) -> None:
        if not text:
            return
        self._last_interaction = text[:80]
        turn = ConversationTurn(role="user", text=text)
        self._conversation.append(turn)

    def _on_jarvis(self, text: str, skill: str | None = None) -> None:
        if not text:
            return
        skill_name = skill.replace("skill:", "") if skill else None
        if skill_name:
            self._skill_counter[skill_name] += 1
        turn = ConversationTurn(role="jarvis", text=text, skill=skill_name)
        self._conversation.append(turn)
        self._last_interaction = text[:80]

    def ask_text(self, text: str) -> ConversationTurn:
        """Consulta por texto (sin micrófono) — usable desde la consola GUI."""
        from jarvis.app.orchestrator import Orchestrator
        from jarvis.brain.hybrid_router import RouteTarget
        from jarvis.events import EventBus
        from jarvis.providers.base import ChatMessage
        from jarvis.skills.base import SkillContext

        t0 = time.perf_counter()
        clear_config_cache()
        cfg = get_config()
        orch = Orchestrator(cfg, EventBus())
        self._on_user(text)
        decision = orch.hybrid.decide(text)
        reply = ""
        skill = None
        sources: list[str] = []
        error = None
        try:
            if decision.target == RouteTarget.SKILL and decision.skill is not None:
                ctx = SkillContext(
                    user_text=text,
                    user_name=cfg.app.user_name,
                    memory=orch.memory,
                    config=orch._skill_config(),
                )
                result = orch.skills.execute(decision.skill, ctx)
                reply = result.message
                skill = decision.skill.name
                self._skill_counter[skill] += 1
                cites = (result.data or {}).get("citations") or []
                sources = [str(c.get("source", c)) for c in cites][:5]
                if not result.success and result.error:
                    error = result.error
            elif decision.target == RouteTarget.MEMORY and orch.memory is not None:
                reply = orch.memory.handle_command(text) or "Listo."
            else:
                system = cfg.llm.system_prompt.format(user_name=cfg.app.user_name)
                messages = [
                    ChatMessage(role="system", content=system),
                    ChatMessage(role="user", content=text),
                ]
                reply = orch.llm.chat(messages).text
        except Exception as exc:  # noqa: BLE001
            reply = f"Error: {exc}"
            error = str(exc)
        elapsed = (time.perf_counter() - t0) * 1000
        self._latencies.append(elapsed)
        turn = ConversationTurn(
            role="error" if error and not reply else "jarvis",
            text=reply,
            elapsed_ms=elapsed,
            skill=skill,
            sources=sources,
            error=error,
        )
        self._conversation.append(turn)
        self._last_interaction = reply[:80]
        self._emit_status()
        return turn

    def conversation(self) -> list[ConversationTurn]:
        return list(self._conversation[-200:])

    # --- status / dashboard ---

    def _ollama_ok(self) -> tuple[bool, str]:
        try:
            url = self.cfg.llm.base_url.rstrip("/") + "/api/tags"
            with httpx.Client(timeout=2.0) as client:
                r = client.get(url)
                if r.status_code == 200:
                    return True, "conectado"
                return False, f"HTTP {r.status_code}"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)[:60]

    def status(self) -> StatusSnapshot:
        clear_config_cache()
        self.cfg = get_config()
        ollama_ok, ollama_detail = self._ollama_ok()
        cpu = ram = None
        if psutil is not None:
            try:
                cpu = float(psutil.cpu_percent(interval=0.05))
                ram = float(psutil.Process().memory_info().rss / (1024 * 1024))
            except Exception:  # noqa: BLE001
                pass
        avg = (
            sum(self._latencies[-20:]) / len(self._latencies[-20:])
            if self._latencies
            else None
        )
        modules = [
            ModuleStatus("Wake", self._wake_active, self.cfg.wake.model),
            ModuleStatus("LLM", True, f"{self.cfg.llm.provider}/{self.cfg.llm.model}"),
            ModuleStatus(
                "Visión",
                self.cfg.vision.enabled,
                f"{self.cfg.vision.provider}/{self.cfg.vision.model}",
            ),
            ModuleStatus("OCR", self.cfg.vision.enabled, self.cfg.vision.ocr_provider),
            ModuleStatus("RAG", self.cfg.rag.enabled, self.cfg.rag.knowledge_dir),
            ModuleStatus("Memoria", self.cfg.memory.enabled, self.cfg.memory.persistent_provider),
            ModuleStatus("Ollama", ollama_ok, ollama_detail),
            ModuleStatus("Micrófono", self._mic_enabled, "on" if self._mic_enabled else "off"),
            ModuleStatus("TTS", True, f"{self.cfg.tts.provider}/{self.cfg.tts.voice}"),
            ModuleStatus(
                "Automatización",
                self.cfg.automation.enabled,
                self.cfg.automation.browser_provider,
            ),
        ]
        return StatusSnapshot(
            running=self._running,
            mic_enabled=self._mic_enabled,
            wake_active=self._wake_active,
            user_name=self.cfg.app.user_name,
            llm=f"{self.cfg.llm.provider}/{self.cfg.llm.model}",
            vision=f"{self.cfg.vision.provider}/{self.cfg.vision.model}",
            ocr=self.cfg.vision.ocr_provider,
            rag="on" if self.cfg.rag.enabled else "off",
            memory="on" if self.cfg.memory.enabled else "off",
            ollama="ok" if ollama_ok else ollama_detail,
            tts=f"{self.cfg.tts.provider}/{self.cfg.tts.voice}",
            automation=self.cfg.automation.browser_provider,
            cpu_percent=cpu,
            ram_mb=ram,
            avg_latency_ms=avg,
            last_interaction=self._last_interaction,
            modules=modules,
        )

    def _resolve(self, maybe: str) -> Path:
        p = Path(maybe)
        return p if p.is_absolute() else project_root() / p

    def dashboard(self) -> DashboardData:
        cfg = get_config()
        notes: list[str] = []
        try:
            db = self._resolve(cfg.memory.db_path)
            if db.exists():
                conn = sqlite3.connect(db)
                rows = conn.execute(
                    "SELECT content FROM memory_items ORDER BY created_at DESC LIMIT 12"
                ).fetchall()
                notes = [r[0][:120] for r in rows]
                conn.close()
        except Exception:  # noqa: BLE001
            pass

        docs: list[str] = []
        try:
            db = self._resolve(cfg.rag.index_db)
            if db.exists():
                conn = sqlite3.connect(db)
                rows = conn.execute(
                    "SELECT path FROM files ORDER BY indexed_at DESC LIMIT 20"
                ).fetchall()
                docs = [Path(r[0]).name for r in rows]
                conn.close()
        except Exception:  # noqa: BLE001
            pass

        automations: list[str] = []
        audit: list[str] = []
        try:
            db = self._resolve(cfg.automation.audit_db)
            if db.exists():
                conn = sqlite3.connect(db)
                rows = conn.execute(
                    "SELECT action, success, description FROM automation_audit "
                    "ORDER BY id DESC LIMIT 15"
                ).fetchall()
                for action, success, desc in rows:
                    line = f"{'✓' if success else '✗'} {action}: {desc[:80]}"
                    automations.append(line)
                    audit.append(line)
                conn.close()
        except Exception:  # noqa: BLE001
            pass

        vision_hist: list[str] = []
        try:
            db = self._resolve(cfg.vision.history_db)
            if db.exists():
                conn = sqlite3.connect(db)
                rows = conn.execute(
                    "SELECT summary, model FROM vision_history ORDER BY id DESC LIMIT 12"
                ).fetchall()
                vision_hist = [
                    f"{(s or '')[:90]} [{m or '—'}]" for s, m in rows
                ]
                conn.close()
        except Exception:  # noqa: BLE001
            pass

        top = self._skill_counter.most_common(8)
        snap = self.status()
        return DashboardData(
            conversations=self.conversation()[-30:],
            memory_notes=notes,
            indexed_docs=docs,
            top_skills=top,
            automations=automations,
            vision_history=vision_hist,
            audit_rows=audit,
            performance={
                "cpu": snap.cpu_percent,
                "ram_mb": snap.ram_mb,
                "avg_latency_ms": snap.avg_latency_ms,
                "turns": len(self._conversation),
            },
        )

    # --- config ---

    def get_config_form(self) -> ConfigForm:
        cfg = get_config()
        return ConfigForm(
            llm_model=cfg.llm.model,
            vision_model=cfg.vision.model,
            vision_provider=cfg.vision.provider,
            ocr_provider=cfg.vision.ocr_provider,
            tts_voice=cfg.tts.voice,
            language=cfg.app.language,
            wake_model=cfg.wake.model,
            wake_threshold=cfg.wake.threshold,
            knowledge_dir=cfg.rag.knowledge_dir,
            rag_chunk_size=cfg.rag.chunk_size,
            rag_chunk_overlap=cfg.rag.chunk_overlap,
            rag_top_k=cfg.rag.top_k,
            llm_provider=cfg.llm.provider,
            browser_provider=cfg.automation.browser_provider,
            volume=cfg.tts.speed,
        )

    def apply_config_form(self, form: ConfigForm) -> str:
        updates = {
            "llm.model": form.llm_model,
            "llm.provider": form.llm_provider,
            "vision.model": form.vision_model,
            "vision.provider": form.vision_provider,
            "vision.ocr_provider": form.ocr_provider,
            "tts.voice": form.tts_voice,
            "tts.speed": form.volume,
            "app.language": form.language,
            "wake.model": form.wake_model,
            "wake.threshold": form.wake_threshold,
            "rag.knowledge_dir": form.knowledge_dir,
            "rag.chunk_size": form.rag_chunk_size,
            "rag.chunk_overlap": form.rag_chunk_overlap,
            "rag.top_k": form.rag_top_k,
            "automation.browser_provider": form.browser_provider,
        }
        save_config_updates(updates)
        clear_config_cache()
        self.cfg = get_config()
        self.notify("Configuración", "Cambios guardados en config.yaml", level="info")
        self._emit_status()
        return "Configuración guardada."

    def recent_logs(self, n: int = 40) -> list[str]:
        log_path = self._resolve(self.cfg.logging.file)
        if not log_path.exists():
            return ["(sin logs aún)"]
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return lines[-n:]
        except Exception as exc:  # noqa: BLE001
            return [f"Error leyendo logs: {exc}"]

    def placeholder_phase8(self) -> list[str]:
        """Huecos listos para Fase 8 (plugins, marketplace, agentes…)."""
        return [
            "Panel de plugins",
            "Marketplace de skills",
            "Gestión de modelos descargados",
            "Agentes especializados",
            "Monitor de tareas en tiempo real",
            "Administración del sistema",
        ]
