"""VisionOrchestrator — captura, analiza, guarda en RAG/historial."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from jarvis.vision.analyzer import DefaultImageAnalyzer
from jarvis.vision.base import CaptureMode, ScreenProvider, VisionAnalysis
from jarvis.vision.history import VisionHistory
from jarvis.vision.ui_locate import UIMatch, find_text_boxes
from jarvis.utils.logging import get_logger


class VisionOrchestrator:
    name = "vision"

    def __init__(
        self,
        *,
        screen: ScreenProvider,
        analyzer: DefaultImageAnalyzer,
        history: VisionHistory | None,
        captures_dir: Path,
        knowledge_dir: Path,
        user_name: str = "Juan",
    ) -> None:
        self.screen = screen
        self.analyzer = analyzer
        self.history = history
        self.captures_dir = captures_dir
        self.knowledge_dir = knowledge_dir
        self.user_name = user_name
        self._log = get_logger("jarvis.vision.orch")
        self.captures_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._last: VisionAnalysis | None = None

    @property
    def last_analysis(self) -> VisionAnalysis | None:
        return self._last

    def _dest(self, prefix: str = "vision") -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return self.captures_dir / f"{prefix}-{stamp}.png"

    def capture(
        self,
        mode: CaptureMode = CaptureMode.FULL,
        *,
        monitor: int | None = None,
        region: tuple[int, int, int, int] | None = None,
    ) -> Path:
        dest = self._dest(mode.value)
        if mode == CaptureMode.ACTIVE_WINDOW:
            cap = self.screen.capture_active_window(dest)
        elif mode == CaptureMode.REGION and region:
            cap = self.screen.capture_region(dest, region)
        elif mode == CaptureMode.MONITOR and monitor is not None:
            cap = self.screen.capture_monitor(dest, monitor)
        else:
            cap = self.screen.capture_full(dest)
        return cap.path

    def analyze_image(
        self,
        image_path: Path,
        question: str,
        *,
        use_ocr: bool = True,
        use_vision: bool = True,
        source: str = "file",
    ) -> VisionAnalysis:
        analysis = self.analyzer.analyze(
            image_path, question, use_ocr=use_ocr, use_vision=use_vision
        )
        analysis.source = source
        if self.history is not None:
            self.history.save(analysis, question=question)
        self._last = analysis
        return analysis

    def describe_screen(
        self,
        question: str = "¿Qué aparece en mi pantalla?",
        *,
        mode: CaptureMode = CaptureMode.FULL,
        monitor: int | None = None,
    ) -> VisionAnalysis:
        path = self.capture(mode, monitor=monitor)
        return self.analyze_image(path, question, source="screen")

    def ocr_only(self, image_path: Path | None = None) -> VisionAnalysis:
        path = image_path or self.capture(CaptureMode.FULL)
        return self.analyze_image(
            path,
            "Lee el texto de esta imagen (OCR).",
            use_ocr=True,
            use_vision=False,
            source="screen" if image_path is None else "file",
        )

    def find_on_screen(self, label: str, *, mode: CaptureMode = CaptureMode.FULL) -> list[UIMatch]:
        path = self.capture(mode)
        analysis = self.analyze_image(
            path,
            f"Localiza el elemento «{label}».",
            use_ocr=True,
            use_vision=False,
            source="screen",
        )
        if not analysis.ocr:
            return []
        return find_text_boxes(analysis.ocr, label)

    def save_to_knowledge(
        self,
        analysis: VisionAnalysis | None = None,
        *,
        title: str | None = None,
    ) -> Path:
        """Guarda OCR+resumen como Markdown en knowledge/ para indexación RAG."""
        analysis = analysis or self._last
        if analysis is None:
            raise ValueError("No hay análisis visual reciente para guardar.")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe = re.sub(r"[^\w\-]+", "-", (title or "captura-vision").lower())[:40]
        md_path = self.knowledge_dir / f"vision-{stamp}-{safe}.md"
        ocr_text = analysis.ocr.text if analysis.ocr else ""
        summary = analysis.vision.summary if analysis.vision else analysis.answer
        body = (
            f"# {title or 'Captura visual'}\n\n"
            f"- Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
            f"- Imagen: `{analysis.image_path}`\n"
            f"- Etiquetas: {', '.join(analysis.tags) or '—'}\n"
            f"- Modelo: {analysis.vision.model if analysis.vision else '—'}\n\n"
            f"## Resumen\n\n{summary}\n\n"
            f"## OCR\n\n{ocr_text or '_(sin texto OCR)_'}\n"
        )
        md_path.write_text(body, encoding="utf-8")
        self._log.info("vision_saved_knowledge", path=str(md_path))

        # Indexación automática si RAG está disponible
        try:
            from jarvis.config import get_config
            from jarvis.rag.factory import build_rag_stack

            cfg = get_config()
            if cfg.rag.enabled:
                indexer, _ = build_rag_stack(cfg)
                indexer.index_path(md_path, force=True)
                self._log.info("vision_indexed_rag", path=str(md_path))
        except Exception as exc:  # noqa: BLE001
            self._log.warning("vision_rag_index_failed", error=str(exc))

        return md_path

    def click_label(
        self,
        label: str,
        mouse_controller,
        *,
        confirmed: bool = False,
    ) -> tuple[bool, str]:
        """Preparación visión→automatización: busca texto OCR y hace clic en el centro."""
        matches = self.find_on_screen(label)
        if not matches:
            return False, f"No encontré «{label}» en pantalla."
        best = max(matches, key=lambda m: m.confidence)
        cx, cy = best.center
        if not confirmed:
            return False, (
                f"Encontré «{best.text}» en ({cx},{cy}). "
                "Di 'confirma' para hacer clic."
            )
        mouse_controller.click(cx, cy)
        return True, f"Hice clic en «{best.text}» ({cx},{cy})."
