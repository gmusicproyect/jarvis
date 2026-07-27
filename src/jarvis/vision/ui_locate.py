"""Localización simple de UI (OCR boxes) para automatización."""

from __future__ import annotations

from dataclasses import dataclass

from jarvis.vision.base import OCRResult


@dataclass
class UIMatch:
    text: str
    x: int
    y: int
    w: int
    h: int
    confidence: float

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2


def find_text_boxes(ocr: OCRResult, query: str, *, min_conf: float = 0.4) -> list[UIMatch]:
    """Busca cajas OCR cuyo texto contenga ``query`` (case-insensitive)."""
    q = query.lower().strip().strip("«»\"'")
    if not q:
        return []
    matches: list[UIMatch] = []
    for box in ocr.boxes:
        text = str(box.get("text", ""))
        conf = float(box.get("conf", 0))
        if conf < min_conf:
            continue
        if q in text.lower():
            matches.append(
                UIMatch(
                    text=text,
                    x=int(box["x"]),
                    y=int(box["y"]),
                    w=int(box["w"]),
                    h=int(box["h"]),
                    confidence=conf,
                )
            )
    return matches
