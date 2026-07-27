"""ImageAnalyzer — combina OCR + Vision LLM."""

from __future__ import annotations

import time
from pathlib import Path

from jarvis.vision.base import (
    ImageAnalyzer,
    OCRProvider,
    OCRResult,
    VisionAnalysis,
    VisionProvider,
)
from jarvis.utils.logging import get_logger


class DefaultImageAnalyzer:
    name = "default"

    def __init__(self, ocr: OCRProvider, vision: VisionProvider) -> None:
        self.ocr = ocr
        self.vision = vision
        self._log = get_logger("jarvis.vision.analyzer")

    def analyze(
        self,
        image_path: Path,
        question: str,
        *,
        use_ocr: bool = True,
        use_vision: bool = True,
    ) -> VisionAnalysis:
        t0 = time.perf_counter()
        ocr_result: OCRResult | None = None
        if use_ocr:
            try:
                ocr_result = self.ocr.extract(image_path)
            except Exception as exc:  # noqa: BLE001
                self._log.warning("ocr_skip", error=str(exc))
                ocr_result = OCRResult(text="", provider="error")

        vision_answer = None
        prompt = self._build_prompt(question, ocr_result)
        if use_vision:
            try:
                vision_answer = self.vision.analyze(image_path, prompt)
            except Exception as exc:  # noqa: BLE001
                self._log.warning("vision_skip", error=str(exc))

        answer = self._compose_answer(question, ocr_result, vision_answer)
        tags = self._tags(question, ocr_result, vision_answer)
        elapsed = (time.perf_counter() - t0) * 1000
        self._log.info(
            "image_analyzed",
            elapsed_ms=round(elapsed, 1),
            ocr_ms=round(ocr_result.elapsed_ms, 1) if ocr_result else None,
            vision_ms=round(vision_answer.elapsed_ms, 1) if vision_answer else None,
            vision_model=vision_answer.model if vision_answer else None,
            ocr_provider=ocr_result.provider if ocr_result else None,
            ocr_confidence=ocr_result.confidence if ocr_result else None,
            source=str(image_path),
        )
        return VisionAnalysis(
            image_path=image_path,
            ocr=ocr_result,
            vision=vision_answer,
            answer=answer,
            tags=tags,
            source="file",
            elapsed_ms=elapsed,
        )

    def _build_prompt(self, question: str, ocr: OCRResult | None) -> str:
        parts = [
            "Eres Jarvis. Analiza la imagen y responde en español, conciso y útil.",
            f"Pregunta del usuario: {question}",
        ]
        if ocr and ocr.text.strip():
            parts.append(
                "Texto OCR detectado (puede tener errores):\n"
                f"{ocr.text[:3000]}"
            )
        parts.append(
            "Si hay errores, botones, tablas o gráficos, descríbelos. "
            "No inventes texto que no se vea."
        )
        return "\n\n".join(parts)

    def _compose_answer(
        self,
        question: str,
        ocr: OCRResult | None,
        vision: object | None,
    ) -> str:
        q = question.lower()
        # Solo OCR pedido
        if any(k in q for k in ("lee el texto", "ocr", "extrae el texto", "qué texto")):
            if ocr and ocr.text.strip():
                conf = (
                    f" (confianza≈{ocr.confidence:.2f})"
                    if ocr.confidence is not None
                    else ""
                )
                return f"Texto detectado{conf}:\n{ocr.text.strip()}"
            if vision and getattr(vision, "summary", ""):
                return getattr(vision, "summary")
            return "No pude extraer texto de la imagen."

        if vision and getattr(vision, "summary", "").strip():
            return getattr(vision, "summary").strip()
        if ocr and ocr.text.strip():
            return f"Solo pude leer OCR:\n{ocr.text.strip()}"
        return "No pude analizar la imagen con los proveedores actuales."

    def _tags(
        self,
        question: str,
        ocr: OCRResult | None,
        vision: object | None,
    ) -> list[str]:
        tags = ["vision"]
        q = question.lower()
        for key, tag in (
            ("error", "error"),
            ("boton", "ui"),
            ("botón", "ui"),
            ("tabla", "table"),
            ("grafico", "chart"),
            ("gráfico", "chart"),
            ("resume", "summary"),
            ("pantalla", "screen"),
        ):
            if key in q:
                tags.append(tag)
        if ocr and ocr.text.strip():
            tags.append("ocr")
        if vision and getattr(vision, "provider", "") not in {"", "stub"}:
            tags.append("vlm")
        return sorted(set(tags))


# Protocol satisfaction hint
_: type[ImageAnalyzer] = DefaultImageAnalyzer
