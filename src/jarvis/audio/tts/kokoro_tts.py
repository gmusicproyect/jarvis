"""TTS Kokoro (mlx-audio) con cancelación cooperativa."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np
import sounddevice as sd

from jarvis.config.loader import TTSConfig
from jarvis.utils.logging import get_logger


def _ensure_espeak_data() -> None:
    """En macOS Homebrew, apunta a datos de espeak-ng si el loader trae rutas rotas."""
    if os.environ.get("ESPEAK_DATA_PATH"):
        return
    candidates = [
        Path("/opt/homebrew/share/espeak-ng-data"),
        Path("/usr/local/share/espeak-ng-data"),
        Path("/usr/share/espeak-ng-data"),
    ]
    for path in candidates:
        if path.exists():
            os.environ["ESPEAK_DATA_PATH"] = str(path)
            return


class KokoroTTS:
    name = "kokoro"

    def __init__(self, cfg: TTSConfig) -> None:
        from mlx_audio.tts.utils import load_model

        _ensure_espeak_data()
        self._cfg = cfg
        self._log = get_logger("jarvis.tts")
        self._model = load_model(model_path=cfg.model)
        self._stopping = False
        self._log.info("tts_loaded", provider="kokoro", voice=cfg.voice)

    def stop(self) -> None:
        self._stopping = True
        try:
            sd.stop()
        except Exception:  # noqa: BLE001
            pass

    def speak(self, text: str, *, cancel_flag: list[bool] | None = None) -> None:
        self._stopping = False
        _ensure_espeak_data()
        try:
            texto = text.replace(". ", ".\n")
            kwargs: dict[str, Any] = dict(
                text=texto,
                voice=self._cfg.voice,
                speed=self._cfg.speed,
                lang_code=self._cfg.lang_code,
            )
            try:
                resultados = self._model.generate(**kwargs, verbose=False)
            except TypeError:
                resultados = self._model.generate(**kwargs)

            rate = int(getattr(self._model, "sample_rate", 24000))
            for result in resultados:
                if self._should_stop(cancel_flag):
                    self.stop()
                    return
                audio = np.array(result.audio, dtype=np.float32)
                sd.play(audio, samplerate=rate)
                duration = float(len(audio)) / float(rate)
                elapsed = 0.0
                step = 0.05
                while elapsed < duration:
                    if self._should_stop(cancel_flag):
                        self.stop()
                        return
                    time.sleep(step)
                    elapsed += step
                sd.wait()
        except Exception as exc:  # noqa: BLE001
            self._log.warning("kokoro_failed_fallback_system", error=str(exc))
            SystemTTS(self._cfg).speak(text, cancel_flag=cancel_flag)

    def _should_stop(self, cancel_flag: list[bool] | None) -> bool:
        return self._stopping or bool(cancel_flag and cancel_flag[0])


class SystemTTS:
    """Respaldo macOS `say` — provider `system`."""

    name = "system"

    def __init__(self, cfg: TTSConfig) -> None:
        self._cfg = cfg
        self._proc: subprocess.Popen[bytes] | None = None

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def speak(self, text: str, *, cancel_flag: list[bool] | None = None) -> None:
        self._proc = subprocess.Popen(["say", text])
        while self._proc.poll() is None:
            if cancel_flag and cancel_flag[0]:
                self.stop()
                return
            try:
                self._proc.wait(timeout=0.1)
            except subprocess.TimeoutExpired:
                continue
