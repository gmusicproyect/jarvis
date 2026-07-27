"""Proveedores de visión multimodal: Ollama, OpenAI, Gemini."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import httpx

from jarvis.vision.base import VisionAnswer
from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.vision.llm")


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


class OllamaVisionProvider:
    name = "ollama"

    def __init__(
        self,
        *,
        model: str = "llava",
        base_url: str = "http://127.0.0.1:11434",
        timeout_s: float = 180.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def analyze(self, image_path: Path, prompt: str) -> VisionAnswer:
        t0 = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [_b64(image_path)],
                }
            ],
            "stream": False,
        }
        with httpx.Client(base_url=self.base_url, timeout=self.timeout_s) as client:
            resp = client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        text = (
            (data.get("message") or {}).get("content")
            or data.get("response")
            or ""
        ).strip()
        elapsed = (time.perf_counter() - t0) * 1000
        _LOG.info(
            "vision_done",
            provider=self.name,
            model=self.model,
            elapsed_ms=round(elapsed, 1),
        )
        return VisionAnswer(
            summary=text,
            details=text,
            provider=self.name,
            model=self.model,
            elapsed_ms=elapsed,
            raw=data if isinstance(data, dict) else {},
        )


class OpenAIVisionProvider:
    name = "openai"

    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        timeout_s: float = 120.0,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def analyze(self, image_path: Path, prompt: str) -> VisionAnswer:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY no configurada")
        t0 = time.perf_counter()
        mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        data_url = f"data:{mime};base64,{_b64(image_path)}"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "max_tokens": 1000,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(base_url=self.base_url, timeout=self.timeout_s) as client:
            resp = client.post("/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        elapsed = (time.perf_counter() - t0) * 1000
        _LOG.info(
            "vision_done",
            provider=self.name,
            model=self.model,
            elapsed_ms=round(elapsed, 1),
        )
        return VisionAnswer(
            summary=text,
            details=text,
            provider=self.name,
            model=self.model,
            elapsed_ms=elapsed,
            raw=data,
        )


class GeminiVisionProvider:
    name = "gemini"

    def __init__(
        self,
        *,
        model: str = "gemini-1.5-flash",
        api_key: str | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or ""
        self.timeout_s = timeout_s

    def analyze(self, image_path: Path, prompt: str) -> VisionAnswer:
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY no configurada")
        t0 = time.perf_counter()
        mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime,
                                "data": _b64(image_path),
                            }
                        },
                    ]
                }
            ]
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(url, params={"key": self.api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            text = str(data)
        elapsed = (time.perf_counter() - t0) * 1000
        _LOG.info(
            "vision_done",
            provider=self.name,
            model=self.model,
            elapsed_ms=round(elapsed, 1),
        )
        return VisionAnswer(
            summary=text,
            details=text,
            provider=self.name,
            model=self.model,
            elapsed_ms=elapsed,
            raw=data,
        )


class StubVisionProvider:
    name = "stub"
    model = "none"

    def analyze(self, image_path: Path, prompt: str) -> VisionAnswer:
        return VisionAnswer(
            summary=(
                "No hay proveedor de visión configurado. "
                "Activa ollama/llava, openai o gemini en config.yaml."
            ),
            provider=self.name,
            model=self.model,
            elapsed_ms=0.0,
        )


def build_vision_provider(
    provider: str,
    *,
    model: str,
    base_url: str,
    api_key: str | None = None,
) -> OllamaVisionProvider | OpenAIVisionProvider | GeminiVisionProvider | StubVisionProvider:
    key = provider.lower().strip()
    if key == "ollama":
        return OllamaVisionProvider(model=model, base_url=base_url)
    if key == "openai":
        return OpenAIVisionProvider(model=model, api_key=api_key)
    if key in {"gemini", "google"}:
        return GeminiVisionProvider(model=model, api_key=api_key)
    _LOG.warning("vision_unknown_provider", provider=provider)
    return StubVisionProvider()
