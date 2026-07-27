"""Tests Fase 6 — visión / OCR / historial / skills."""

from __future__ import annotations

from pathlib import Path

from jarvis.skills.base import SkillContext
from jarvis.skills.builtin.describe_screen import DescribeScreenSkill
from jarvis.skills.builtin.ocr_image import OcrImageSkill
from jarvis.skills.builtin.save_to_knowledge import SaveToKnowledgeSkill
from jarvis.skills.manager import SkillManager
from jarvis.vision.analyzer import DefaultImageAnalyzer
from jarvis.vision.base import CaptureMode, OCRResult, ScreenCapture, VisionAnswer
from jarvis.vision.history import VisionHistory
from jarvis.vision.orchestrator import VisionOrchestrator
from jarvis.vision.ui_locate import find_text_boxes


class FakeOCR:
    name = "fake_ocr"

    def extract(self, image_path: Path, *, languages: list[str] | None = None) -> OCRResult:
        return OCRResult(
            text="Error: connection refused\nBotón Continuar",
            confidence=0.91,
            provider=self.name,
            elapsed_ms=12.0,
            boxes=[
                {
                    "text": "Continuar",
                    "x": 100,
                    "y": 200,
                    "w": 80,
                    "h": 24,
                    "conf": 0.95,
                }
            ],
        )


class FakeVision:
    name = "fake_vision"
    model = "fake-vlm"

    def analyze(self, image_path: Path, prompt: str) -> VisionAnswer:
        return VisionAnswer(
            summary="La pantalla muestra un error de conexión y un botón Continuar.",
            provider=self.name,
            model=self.model,
            elapsed_ms=40.0,
        )


class FakeScreen:
    name = "fake_screen"

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp

    def _shot(self, dest: Path, mode: CaptureMode) -> ScreenCapture:
        dest.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        return ScreenCapture(path=dest, mode=mode, elapsed_ms=5.0)

    def capture_full(self, dest: Path) -> ScreenCapture:
        return self._shot(dest, CaptureMode.FULL)

    def capture_active_window(self, dest: Path) -> ScreenCapture:
        return self._shot(dest, CaptureMode.ACTIVE_WINDOW)

    def capture_region(
        self, dest: Path, region: tuple[int, int, int, int]
    ) -> ScreenCapture:
        cap = self._shot(dest, CaptureMode.REGION)
        cap.region = region
        return cap

    def capture_monitor(self, dest: Path, monitor: int) -> ScreenCapture:
        cap = self._shot(dest, CaptureMode.MONITOR)
        cap.monitor = monitor
        return cap


def _orch(tmp: Path) -> VisionOrchestrator:
    return VisionOrchestrator(
        screen=FakeScreen(tmp),
        analyzer=DefaultImageAnalyzer(FakeOCR(), FakeVision()),
        history=VisionHistory(tmp / "vision.db"),
        captures_dir=tmp / "shots",
        knowledge_dir=tmp / "knowledge",
    )


def test_describe_screen(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    analysis = orch.describe_screen("¿Qué hay en mi pantalla?")
    assert "error" in analysis.answer.lower() or "Continuar" in analysis.answer
    assert analysis.history_id is not None
    assert analysis.ocr is not None
    assert analysis.ocr.confidence == 0.91


def test_ocr_only(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    analysis = orch.ocr_only()
    assert "Continuar" in analysis.answer or "connection" in analysis.answer.lower()


def test_find_text_boxes() -> None:
    ocr = OCRResult(
        text="x",
        boxes=[{"text": "Aceptar", "x": 10, "y": 10, "w": 40, "h": 12, "conf": 0.9}],
    )
    hits = find_text_boxes(ocr, "aceptar")
    assert len(hits) == 1
    assert hits[0].center == (30, 16)


def test_save_to_knowledge(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    orch.describe_screen("resume")
    path = orch.save_to_knowledge(title="Demo slide")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "OCR" in content
    assert "Resumen" in content


def test_vision_skills_registered() -> None:
    mgr = SkillManager(plugin_dirs=[])
    mgr.load_builtin()
    names = {s.name for s in mgr.skills}
    for required in (
        "describe_screen",
        "ocr_image",
        "read_screen",
        "analyze_image",
        "save_to_knowledge",
        "find_on_screen",
    ):
        assert required in names


def test_describe_skill_score() -> None:
    assert DescribeScreenSkill().can_handle("¿Qué hay en mi pantalla?") >= 0.8
    assert OcrImageSkill().can_handle("Lee el texto de esta imagen") >= 0.8
    assert SaveToKnowledgeSkill().can_handle("Guarda esta captura en mi base de conocimiento") >= 0.8


def test_describe_skill_execute(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    skill = DescribeScreenSkill()
    result = skill.execute(
        SkillContext(user_text="¿Qué hay en mi pantalla?", config={"vision": orch})
    )
    assert result.success
    assert result.data.get("history_id")
