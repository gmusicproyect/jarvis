"""Cliente Ollama (HTTP local)."""

from __future__ import annotations

import httpx

from jarvis.config.loader import LLMConfig
from jarvis.providers.base import ChatMessage, LLMResponse
from jarvis.utils.logging import get_logger


class OllamaProvider:
    name = "ollama"

    def __init__(self, cfg: LLMConfig) -> None:
        self._cfg = cfg
        self._log = get_logger("jarvis.llm")
        self._client = httpx.Client(base_url=cfg.base_url.rstrip("/"), timeout=cfg.timeout_s)

    def chat(self, messages: list[ChatMessage]) -> LLMResponse:
        payload = {
            "model": self._cfg.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": self._cfg.temperature},
        }
        self._log.info("ollama_request", model=self._cfg.model, turns=len(messages))
        response = self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        text = data.get("message", {}).get("content", "").strip()
        return LLMResponse(text=text, model=self._cfg.model, provider=self.name)

    def close(self) -> None:
        self._client.close()
