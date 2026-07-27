"""Contratos (Protocol) para providers de audio y LLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


AudioInt16 = NDArray[np.int16]
AudioFloat32 = NDArray[np.float32]


@dataclass(frozen=True)
class Transcript:
    text: str
    language: str | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class ChatMessage:
    role: str  # system | user | assistant
    content: str


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    provider: str


@runtime_checkable
class WakeProvider(Protocol):
    """Detecta la frase de activación sobre chunks de audio int16."""

    name: str

    def reset(self) -> None: ...

    def score(self, chunk: AudioInt16) -> float: ...

    def detected(self, chunk: AudioInt16, threshold: float) -> bool: ...


@runtime_checkable
class STTProvider(Protocol):
    name: str

    def transcribe(self, audio: AudioFloat32, sample_rate: int) -> Transcript: ...


@runtime_checkable
class TTSProvider(Protocol):
    name: str

    def speak(self, text: str, *, cancel_flag: list[bool] | None = None) -> None:
        """Reproduce voz. Si cancel_flag[0] es True, debe detenerse."""
        ...

    def stop(self) -> None: ...


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def chat(self, messages: list[ChatMessage]) -> LLMResponse: ...
