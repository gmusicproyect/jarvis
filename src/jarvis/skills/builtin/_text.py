"""Utilidades de texto para skills."""

from __future__ import annotations

import re
from unicodedata import normalize


def norm(text: str) -> str:
    folded = normalize("NFD", text.lower())
    return "".join(c for c in folded if c.isalnum() or c.isspace()).strip()


def score_keywords(text: str, keywords: list[str], *, boost: float = 0.85) -> float:
    n = norm(text)
    hits = sum(1 for k in keywords if k in n)
    if hits == 0:
        return 0.0
    return min(1.0, boost + 0.05 * (hits - 1))


def extract_url(text: str) -> str | None:
    m = re.search(r"https?://\S+", text, re.I)
    if m:
        return m.group(0).rstrip(".,)")
    m = re.search(r"\b([\w-]+\.(?:com|org|net|io|es|dev|app))\b", text, re.I)
    if m:
        return "https://" + m.group(1)
    return None


def extract_minutes(text: str) -> int | None:
    m = re.search(r"(\d+)\s*(?:minutos|minuto|mins|min)", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*(?:segundos|segundo|segs|seg)", text, re.I)
    if m:
        return max(1, int(m.group(1)) // 60) or 1
    m = re.search(r"(\d+)\s*(?:horas|hora|h)\b", text, re.I)
    if m:
        return int(m.group(1)) * 60
    return None
