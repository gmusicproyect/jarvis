"""Captura de enunciados con VAD por umbral de energía."""

from __future__ import annotations

import time

import numpy as np
import sounddevice as sd
from numpy.typing import NDArray

from jarvis.config.loader import CaptureConfig, WakeConfig


def capture_utterance(
    stream: sd.InputStream,
    capture: CaptureConfig,
    wake: WakeConfig,
    *,
    max_wait_s: float | None = None,
) -> NDArray[np.float32] | None:
    """Graba desde que hay voz hasta silencio. None si no habla a tiempo."""
    chunk = wake.chunk_samples
    rate = wake.sample_rate
    wait_s = max_wait_s if max_wait_s is not None else capture.wait_voice_s

    frames: list[NDArray[np.int16]] = []
    silence = 0.0
    started = False
    t0 = time.time()

    while True:
        data, _overflow = stream.read(chunk)
        audio = np.squeeze(data).astype(np.int16)
        frames.append(audio)
        vol = int(np.abs(audio).max())
        elapsed = time.time() - t0

        if vol > capture.voice_threshold:
            started = True
            silence = 0.0
        else:
            silence += chunk / rate

        if not started and elapsed > wait_s:
            return None
        if started and silence > capture.silence_max_s:
            break
        if elapsed > capture.max_utterance_s:
            break

    raw = np.concatenate(frames).astype(np.float32) / 32768.0
    return raw
