"""STT con faster-whisper."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from jarvis.config.loader import STTConfig
from jarvis.providers.base import Transcript
from jarvis.utils.logging import get_logger


class FasterWhisperSTT:
    name = "faster_whisper"

    def __init__(self, cfg: STTConfig) -> None:
        from faster_whisper import WhisperModel

        self._cfg = cfg
        self._log = get_logger("jarvis.stt")
        self._model = WhisperModel(
            cfg.model_size,
            device=cfg.device,
            compute_type=cfg.compute_type,
        )
        self._log.info("stt_loaded", model=cfg.model_size)

    def transcribe(self, audio: NDArray[np.float32], sample_rate: int) -> Transcript:
        # sample_rate documentado; faster-whisper espera 16 kHz típico
        _ = sample_rate
        language = self._cfg.language
        kwargs: dict[str, object] = {"vad_filter": True}
        if self._cfg.auto_detect_english:
            # Dejamos que el modelo detecte; priorizamos es en prompt interno
            kwargs["language"] = None
        else:
            kwargs["language"] = language

        segments, info = self._model.transcribe(audio, **kwargs)  # type: ignore[arg-type]
        text = " ".join(s.text for s in segments).strip()
        detected = getattr(info, "language", language)
        # Si detecta inglés y auto_detect está on, aceptar; si no, forzar es en re-run simple
        if (
            not self._cfg.auto_detect_english
            and detected
            and detected != language
        ):
            segments, info = self._model.transcribe(audio, language=language, vad_filter=True)
            text = " ".join(s.text for s in segments).strip()
            detected = language
        elif self._cfg.auto_detect_english and detected not in {language, "en", None}:
            # Preferir español si la detección es rara
            segments, info = self._model.transcribe(audio, language=language, vad_filter=True)
            text = " ".join(s.text for s in segments).strip()
            detected = language

        self._log.info("stt_done", chars=len(text), language=detected)
        return Transcript(text=text, language=str(detected) if detected else None)
