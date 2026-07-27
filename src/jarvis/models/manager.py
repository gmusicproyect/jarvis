"""Model Manager — listar / pull / remove vía Ollama."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from jarvis.utils.logging import get_logger


@dataclass
class ModelInfo:
    name: str
    size_bytes: int = 0
    family: str = ""
    kind: str = "llm"  # llm | vision | embedding | other

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024**3) if self.size_bytes else 0.0


class ModelManager:
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url.rstrip("/")
        self._log = get_logger("jarvis.models")

    def list(self) -> list[ModelInfo]:
        with httpx.Client(base_url=self.base_url, timeout=10.0) as client:
            resp = client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
        out: list[ModelInfo] = []
        for m in data.get("models", []):
            name = m.get("name") or m.get("model") or ""
            size = int(m.get("size") or 0)
            details = m.get("details") or {}
            family = str(details.get("family") or "")
            out.append(
                ModelInfo(
                    name=name,
                    size_bytes=size,
                    family=family,
                    kind=self._classify(name, family),
                )
            )
        return out

    def _classify(self, name: str, family: str) -> str:
        low = f"{name} {family}".lower()
        if any(x in low for x in ("embed", "nomic", "bge", "minilm")):
            return "embedding"
        if any(x in low for x in ("llava", "vision", "vl", "qwen2.5vl", "bakllava")):
            return "vision"
        return "llm"

    def pull(self, name: str) -> str:
        self._log.info("model_pull_start", name=name)
        with httpx.Client(base_url=self.base_url, timeout=None) as client:
            with client.stream("POST", "/api/pull", json={"name": name}) as resp:
                resp.raise_for_status()
                last = ""
                for line in resp.iter_lines():
                    if line:
                        last = line
        self._log.info("model_pull_done", name=name)
        return f"Modelo '{name}' descargado."

    def remove(self, name: str) -> str:
        with httpx.Client(base_url=self.base_url, timeout=60.0) as client:
            resp = client.delete("/api/delete", json={"name": name})
            # algunas versiones usan POST
            if resp.status_code == 404:
                resp = client.post("/api/delete", json={"name": name})
            resp.raise_for_status()
        self._log.info("model_removed", name=name)
        return f"Modelo '{name}' eliminado."
