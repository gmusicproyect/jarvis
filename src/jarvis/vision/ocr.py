"""OCR providers: Tesseract y EasyOCR."""

from __future__ import annotations

import time
from pathlib import Path

from jarvis.vision.base import OCRResult
from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.vision.ocr")


class TesseractOCRProvider:
    name = "tesseract"

    def __init__(self, *, languages: list[str] | None = None) -> None:
        self.languages = languages or ["spa", "eng"]

    def extract(self, image_path: Path, *, languages: list[str] | None = None) -> OCRResult:
        t0 = time.perf_counter()
        langs = languages or self.languages
        lang_arg = "+".join(langs)
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "OCR Tesseract requiere: poetry add pytesseract Pillow "
                "y `brew install tesseract tesseract-lang`"
            ) from exc

        img = Image.open(image_path)
        try:
            data = pytesseract.image_to_data(img, lang=lang_arg, output_type=pytesseract.Output.DICT)
            texts: list[str] = []
            boxes: list[dict] = []
            confs: list[float] = []
            n = len(data.get("text", []))
            for i in range(n):
                word = (data["text"][i] or "").strip()
                if not word:
                    continue
                conf = float(data["conf"][i])
                if conf < 0:
                    continue
                texts.append(word)
                confs.append(conf)
                boxes.append(
                    {
                        "text": word,
                        "x": int(data["left"][i]),
                        "y": int(data["top"][i]),
                        "w": int(data["width"][i]),
                        "h": int(data["height"][i]),
                        "conf": conf / 100.0,
                    }
                )
            text = " ".join(texts)
            # también bloque completo
            if not text:
                text = pytesseract.image_to_string(img, lang=lang_arg).strip()
            avg_conf = (sum(confs) / len(confs) / 100.0) if confs else None
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("tesseract_failed", error=str(exc))
            raise

        elapsed = (time.perf_counter() - t0) * 1000
        _LOG.info(
            "ocr_done",
            provider=self.name,
            chars=len(text),
            confidence=avg_conf,
            elapsed_ms=round(elapsed, 1),
        )
        return OCRResult(
            text=text,
            confidence=avg_conf,
            language=lang_arg,
            provider=self.name,
            elapsed_ms=elapsed,
            boxes=boxes,
        )


class EasyOCRProvider:
    name = "easyocr"

    def __init__(self, *, languages: list[str] | None = None) -> None:
        # EasyOCR usa códigos cortos: es, en
        raw = languages or ["es", "en"]
        self.languages = [_easy_lang(x) for x in raw]
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            try:
                import easyocr
            except ImportError as exc:
                raise RuntimeError(
                    "OCR EasyOCR requiere: poetry add easyocr"
                ) from exc
            self._reader = easyocr.Reader(self.languages, gpu=False)
        return self._reader

    def extract(self, image_path: Path, *, languages: list[str] | None = None) -> OCRResult:
        t0 = time.perf_counter()
        reader = self._get_reader()
        results = reader.readtext(str(image_path))
        texts: list[str] = []
        boxes: list[dict] = []
        confs: list[float] = []
        for bbox, text, conf in results:
            text = (text or "").strip()
            if not text:
                continue
            texts.append(text)
            confs.append(float(conf))
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            x, y = int(min(xs)), int(min(ys))
            w, h = int(max(xs) - x), int(max(ys) - y)
            boxes.append(
                {"text": text, "x": x, "y": y, "w": w, "h": h, "conf": float(conf)}
            )
        joined = "\n".join(texts)
        avg = sum(confs) / len(confs) if confs else None
        elapsed = (time.perf_counter() - t0) * 1000
        _LOG.info(
            "ocr_done",
            provider=self.name,
            chars=len(joined),
            confidence=avg,
            elapsed_ms=round(elapsed, 1),
        )
        return OCRResult(
            text=joined,
            confidence=avg,
            language="+".join(self.languages),
            provider=self.name,
            elapsed_ms=elapsed,
            boxes=boxes,
        )


class StubOCRProvider:
    """Fallback cuando no hay motor OCR instalado."""

    name = "stub"

    def extract(self, image_path: Path, *, languages: list[str] | None = None) -> OCRResult:
        return OCRResult(
            text="",
            confidence=None,
            language="spa+eng",
            provider=self.name,
            elapsed_ms=0.0,
            boxes=[],
        )


def _easy_lang(code: str) -> str:
    mapping = {"spa": "es", "eng": "en", "es": "es", "en": "en"}
    return mapping.get(code.lower(), code.lower())


def build_ocr_provider(name: str, languages: list[str]):
    key = name.lower().strip()
    if key == "tesseract":
        try:
            import pytesseract  # noqa: F401
            from PIL import Image  # noqa: F401

            return TesseractOCRProvider(languages=languages)
        except ImportError:
            _LOG.warning("tesseract_deps_missing_using_stub")
            return StubOCRProvider()
    if key == "easyocr":
        try:
            import easyocr  # noqa: F401

            return EasyOCRProvider(languages=languages)
        except ImportError:
            _LOG.warning("easyocr_missing_using_stub")
            return StubOCRProvider()
    if key == "stub":
        return StubOCRProvider()
    _LOG.warning("ocr_unknown_provider", name=name)
    return StubOCRProvider()
