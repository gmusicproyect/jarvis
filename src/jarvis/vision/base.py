"""Contratos Vision — OCR, Screen, Vision LLM, Analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable


class CaptureMode(str, Enum):
    FULL = "full"
    ACTIVE_WINDOW = "active_window"
    REGION = "region"
    MONITOR = "monitor"


@dataclass
class OCRResult:
    text: str
    confidence: float | None = None
    language: str = "spa+eng"
    provider: str = ""
    elapsed_ms: float = 0.0
    boxes: list[dict] = field(default_factory=list)  # {text,x,y,w,h,conf}


@dataclass
class VisionAnswer:
    summary: str
    details: str = ""
    provider: str = ""
    model: str = ""
    elapsed_ms: float = 0.0
    raw: dict = field(default_factory=dict)


@dataclass
class ScreenCapture:
    path: Path
    mode: CaptureMode
    monitor: int | None = None
    region: tuple[int, int, int, int] | None = None  # x,y,w,h
    elapsed_ms: float = 0.0


@dataclass
class VisionAnalysis:
    image_path: Path
    ocr: OCRResult | None
    vision: VisionAnswer | None
    answer: str
    tags: list[str] = field(default_factory=list)
    source: str = "screen"  # screen | file | clipboard
    elapsed_ms: float = 0.0
    history_id: int | None = None


@runtime_checkable
class OCRProvider(Protocol):
    name: str

    def extract(self, image_path: Path, *, languages: list[str] | None = None) -> OCRResult: ...


@runtime_checkable
class ScreenProvider(Protocol):
    name: str

    def capture_full(self, dest: Path) -> ScreenCapture: ...

    def capture_active_window(self, dest: Path) -> ScreenCapture: ...

    def capture_region(
        self, dest: Path, region: tuple[int, int, int, int]
    ) -> ScreenCapture: ...

    def capture_monitor(self, dest: Path, monitor: int) -> ScreenCapture: ...


@runtime_checkable
class VisionProvider(Protocol):
    name: str
    model: str

    def analyze(self, image_path: Path, prompt: str) -> VisionAnswer: ...


@runtime_checkable
class ImageAnalyzer(Protocol):
    name: str

    def analyze(
        self,
        image_path: Path,
        question: str,
        *,
        use_ocr: bool = True,
        use_vision: bool = True,
    ) -> VisionAnalysis: ...
