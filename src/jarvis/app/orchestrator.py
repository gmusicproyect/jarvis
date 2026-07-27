"""Orquestador del loop de voz — Fase 1."""

from __future__ import annotations

import subprocess
import threading
import time
from enum import Enum

import numpy as np
import sounddevice as sd

from jarvis.automation.factory import build_automation_engine
from jarvis.audio.capture import capture_utterance
from jarvis.brain.hybrid_router import HybridRouter, RouteTarget
from jarvis.brain.intent import IntentRouter
from jarvis.config.loader import JarvisConfig, project_root
from jarvis.events import (
    FOLLOWUP_ENDED,
    FOLLOWUP_STARTED,
    INTENT_ROUTED,
    LLM_RESPONSE_READY,
    SPEECH_RECOGNIZED,
    STATE_CHANGED,
    TTS_CANCELLED,
    TTS_FINISHED,
    TTS_STARTED,
    WAKE_DETECTED,
    EventBus,
)
from jarvis.memory.factory import build_memory_service
from jarvis.memory.service import MemoryService
from jarvis.providers.base import ChatMessage, LLMProvider, STTProvider, TTSProvider, WakeProvider
from jarvis.providers.factory import build_llm, build_stt, build_tts, build_wake
from jarvis.skills.base import SkillContext
from jarvis.skills.manager import SkillManager
from jarvis.utils.logging import get_logger
from jarvis.utils.metrics import MetricsCollector
from jarvis.vision.factory import build_vision_stack


class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    FOLLOWUP = "followup"


class Orchestrator:
    def __init__(self, cfg: JarvisConfig, bus: EventBus | None = None) -> None:
        self.cfg = cfg
        self.bus = bus or EventBus()
        self.log = get_logger("jarvis.orchestrator")
        self.metrics = MetricsCollector(
            self.bus,
            enabled=cfg.metrics.enabled,
            log_system=cfg.metrics.log_system_usage,
        )
        self.wake: WakeProvider = build_wake(cfg)
        self.stt: STTProvider = build_stt(cfg)
        self.tts: TTSProvider = build_tts(cfg)
        self.llm: LLMProvider = build_llm(cfg)
        self.router = IntentRouter(cfg.session)
        self.memory: MemoryService | None = build_memory_service(cfg)
        self._cancel: list[bool] = [False]
        self.automation = (
            build_automation_engine(cfg, cancel_flag=self._cancel)
            if cfg.automation.enabled
            else None
        )
        self.vision = build_vision_stack(cfg)
        self.skills = SkillManager(
            plugin_dirs=[project_root() / cfg.skills.plugin_dir],
            allow_restricted=cfg.security.allow_restricted,
        )
        if cfg.skills.enabled:
            self.skills.discover()
            # Plugins empaquetados (manifest.yaml)
            try:
                from jarvis.plugins.manager import PluginManager

                pm = PluginManager(project_root() / "plugins")
                for skill in pm.load_skills():
                    self.skills.register(skill)
            except Exception as exc:  # noqa: BLE001
                self.log.warning("plugins_load_failed", error=str(exc))
        try:
            from jarvis.hardening.recovery import register_default_recoveries

            register_default_recoveries(cfg)
        except Exception:  # noqa: BLE001
            pass
        self.hybrid = HybridRouter(
            self.router,
            self.skills,
            llm=self.llm if cfg.skills.use_llm_router else None,
            llm_threshold=cfg.skills.min_score,
        )
        self._state = State.IDLE
        self._stop = False

    def _set_state(self, state: State) -> None:
        self._state = state
        self.bus.publish(STATE_CHANGED, state=state.value)

    def _ding(self) -> None:
        sound = self.cfg.paths.activation_sound
        self.log.info("activation_sound", path=sound)
        subprocess.run(["afplay", "-v", "2", sound], check=False)

    def _is_cancel_text(self, text: str) -> bool:
        return self.hybrid.decide(text).target == RouteTarget.CANCEL

    def _skill_config(self) -> dict:
        if not hasattr(self, "_rag_session_cache"):
            self._rag_session_cache: dict = {}
        cfg: dict = {
            "weather": dict(self.cfg.skills.weather),
            "news": dict(self.cfg.skills.news),
            "rag_session_cache": self._rag_session_cache,
        }
        if self.automation is not None:
            cfg["automation"] = self.automation
        if self.vision is not None:
            cfg["vision"] = self.vision
        return cfg

    def _handle_query(self, stream: sd.InputStream, text: str) -> None:
        decision = self.hybrid.decide(text)
        self.bus.publish(
            INTENT_ROUTED,
            kind=decision.target.value,
            text=text,
            source=decision.source,
            skill=decision.skill.name if decision.skill else None,
        )

        if decision.target == RouteTarget.EMPTY:
            return
        if decision.target == RouteTarget.CANCEL:
            self.skills.cancel_pending()
            if self.automation is not None:
                self.automation.cancel_pending()
            self._cancel[0] = True
            self.tts.stop()
            self.bus.publish(TTS_CANCELLED, reason="user_command")
            return

        if decision.target == RouteTarget.CONFIRM:
            result = self.skills.confirm_pending()
            if result is None and self.automation is not None:
                ar = self.automation.confirm_pending()
                if ar is not None:
                    from jarvis.skills.base import SkillResult

                    result = SkillResult(ar.success, ar.message, data=dict(ar.data))
            if result is None:
                self._speak_reply(stream, "No hay ninguna acción pendiente de confirmar.")
                return
            self._speak_reply(stream, result.message)
            return

        self._set_state(State.THINKING)

        if decision.target == RouteTarget.MEMORY and self.memory is not None:
            mem_reply = self.memory.handle_command(text)
            if mem_reply is not None:
                self.memory.session.add("user", text)
                self.memory.session.add("assistant", mem_reply)
                self.bus.publish(LLM_RESPONSE_READY, text=mem_reply, model="memory")
                self._speak_reply(stream, mem_reply)
                return

        if decision.target == RouteTarget.SKILL and decision.skill is not None:
            user_name = self.cfg.app.user_name
            if self.memory is not None:
                user_name = self.memory.persistent.get_profile("name") or user_name
            ctx = SkillContext(
                user_text=text,
                user_name=user_name,
                memory=self.memory,
                config=self._skill_config(),
            )
            result = self.skills.execute(decision.skill, ctx)
            if self.memory is not None:
                self.memory.session.add("user", text)
                self.memory.session.add("assistant", result.message)
            self.bus.publish(
                LLM_RESPONSE_READY,
                text=result.message,
                model=f"skill:{decision.skill.name}",
            )
            self._speak_reply(stream, result.message)
            return

        # Chat LLM con memoria de sesión + contexto
        user_name = self.cfg.app.user_name
        if self.memory is not None:
            user_name = self.memory.persistent.get_profile("name") or user_name

        system = self.cfg.llm.system_prompt.format(user_name=user_name)
        messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]

        if self.memory is not None:
            ctx = self.memory.context_for_llm(text)
            if ctx:
                messages.append(
                    ChatMessage(
                        role="system",
                        content="Contexto de memoria (usa solo si es relevante):\n" + ctx,
                    )
                )
            for turn in self.memory.session.history():
                messages.append(ChatMessage(role=turn.role, content=turn.content))

        messages.append(ChatMessage(role="user", content=text))

        with self.metrics.measure("llm_ms"):
            reply = self.llm.chat(messages)
        self.bus.publish(LLM_RESPONSE_READY, text=reply.text, model=reply.model)
        self.log.info("llm_reply", chars=len(reply.text))

        if self.memory is not None:
            self.memory.session.add("user", text)
            self.memory.session.add("assistant", reply.text)

        self._speak_reply(stream, reply.text)

    def _monitor_cancel(self, _stream: sd.InputStream) -> None:
        """Hilo: escucha cancelación por voz durante TTS (stream propio)."""
        chunk = self.cfg.wake.chunk_samples
        rate = self.cfg.wake.sample_rate
        buf: list[np.ndarray] = []
        samples_needed = int(rate * 1.2)
        try:
            with sd.InputStream(
                samplerate=rate,
                channels=1,
                dtype="int16",
                blocksize=chunk,
            ) as mic:
                while self._state == State.SPEAKING and not self._cancel[0]:
                    data, _ = mic.read(chunk)
                    audio = np.squeeze(data)
                    buf.append(audio)
                    total = sum(len(x) for x in buf)
                    if total < samples_needed:
                        continue
                    raw = np.concatenate(buf).astype(np.float32) / 32768.0
                    buf.clear()
                    try:
                        tr = self.stt.transcribe(raw, rate)
                    except Exception:  # noqa: BLE001
                        continue
                    if tr.text and self._is_cancel_text(tr.text):
                        self.log.info("voice_cancel", text=tr.text)
                        self._cancel[0] = True
                        self.tts.stop()
                        break
        except Exception as exc:  # noqa: BLE001
            self.log.warning("cancel_monitor_failed", error=str(exc))

    def _speak_reply(self, stream: sd.InputStream, reply_text: str) -> None:
        self._cancel[0] = False
        self._set_state(State.SPEAKING)
        self.bus.publish(TTS_STARTED, text=reply_text)
        monitor = threading.Thread(
            target=self._monitor_cancel, args=(stream,), daemon=True
        )
        monitor.start()
        with self.metrics.measure("tts_ms"):
            self.tts.speak(reply_text, cancel_flag=self._cancel)
        monitor.join(timeout=0.2)
        if self._cancel[0]:
            self.bus.publish(TTS_CANCELLED, reason="interrupted")
        else:
            self.bus.publish(TTS_FINISHED)

    def _listen_and_process(self, stream: sd.InputStream, *, followup: bool) -> None:
        self._set_state(State.FOLLOWUP if followup else State.LISTENING)
        wait = self.cfg.session.followup_seconds if followup else None
        audio = capture_utterance(
            stream,
            self.cfg.capture,
            self.cfg.wake,
            max_wait_s=wait,
        )
        if audio is None:
            if followup:
                self.bus.publish(FOLLOWUP_ENDED, reason="timeout")
            return

        with self.metrics.measure("stt_ms"):
            transcript = self.stt.transcribe(audio, self.cfg.wake.sample_rate)
        self.bus.publish(SPEECH_RECOGNIZED, text=transcript.text)
        self.log.info("user_said", text=transcript.text)
        if not transcript.text:
            return
        self._handle_query(stream, transcript.text)

        # Follow-up mode tras responder
        if self.cfg.session.followup_enabled and not self._cancel[0]:
            self.bus.publish(FOLLOWUP_STARTED, seconds=self.cfg.session.followup_seconds)
            self._listen_and_process(stream, followup=True)

    def run(self) -> None:
        self.log.info(
            "orchestrator_start",
            wake=self.cfg.wake.provider,
            stt=self.cfg.stt.provider,
            llm=self.cfg.llm.provider,
            tts=self.cfg.tts.provider,
            voice=self.cfg.tts.voice,
        )
        # Saludo
        self._set_state(State.SPEAKING)
        name = self.cfg.app.user_name
        if self.memory is not None:
            name = self.memory.persistent.get_profile("name") or name
        greet = f"Jarvis en línea, {name}."
        self.tts.speak(greet)
        self._set_state(State.IDLE)

        chunk = self.cfg.wake.chunk_samples
        rate = self.cfg.wake.sample_rate
        clap_times: list[float] = []
        last_peak = 0.0

        print(
            f"\nJarvis listo. Di 'Hey Jarvis' "
            f"(J inglesa) o aplaude {self.cfg.session.clap_count} veces. Ctrl+C sale.\n"
        )

        with sd.InputStream(
            samplerate=rate,
            channels=1,
            dtype="int16",
            blocksize=chunk,
        ) as stream:
            while not self._stop:
                data, _ = stream.read(chunk)
                audio = np.squeeze(data)
                vol = int(np.abs(audio).max())
                now = time.time()

                if self.cfg.session.clap_enabled:
                    if vol > self.cfg.session.clap_threshold and (now - last_peak) > 0.25:
                        last_peak = now
                        clap_times = [
                            t
                            for t in clap_times
                            if now - t < self.cfg.session.clap_window_s
                        ] + [now]

                t_wake = time.perf_counter()
                score = self.wake.score(audio)
                wake_hit = score > self.cfg.wake.threshold
                clap_hit = (
                    self.cfg.session.clap_enabled
                    and len(clap_times) >= self.cfg.session.clap_count
                )

                if wake_hit or clap_hit:
                    self.metrics.begin_turn()
                    self.metrics.record(
                        "wake_detect_ms",
                        (time.perf_counter() - t_wake) * 1000,
                    )
                    clap_times.clear()
                    self.bus.publish(
                        WAKE_DETECTED,
                        score=score,
                        via="clap" if clap_hit and not wake_hit else "wake",
                    )
                    self.log.info("wake_detected", score=round(score, 3))
                    self._ding()
                    try:
                        stream.abort()
                        stream.start()
                    except Exception:  # noqa: BLE001
                        pass
                    self.wake.reset()
                    try:
                        self._listen_and_process(stream, followup=False)
                    except Exception as exc:  # noqa: BLE001
                        self.log.exception("turn_failed", error=str(exc))
                    finally:
                        self.metrics.end_turn()
                        self.wake.reset()
                        self._set_state(State.IDLE)
                        self._cancel[0] = False
                        print("\n(Escuchando... Hey Jarvis)")

    def stop(self) -> None:
        self._stop = True
        self.tts.stop()
