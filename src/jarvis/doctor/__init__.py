"""Diagnóstico automático del entorno Jarvis."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from jarvis.config import JarvisConfig, project_root
from jarvis.release import PRODUCT_NAME, read_version_file


class CheckLevel(str, Enum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    name: str
    level: CheckLevel
    message: str
    detail: str = ""


@dataclass
class DoctorReport:
    product: str
    version: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(1 for c in self.checks if c.level == CheckLevel.OK)

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.level == CheckLevel.WARN)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.level == CheckLevel.FAIL)

    def exit_code(self) -> int:
        if self.fail_count:
            return 2
        if self.warn_count:
            return 1
        return 0


def _disk_free_gb(path: Path) -> float:
    usage = shutil.disk_usage(path)
    return usage.free / (1024**3)


def _check_python() -> CheckResult:
    major, minor = sys.version_info[:2]
    ver = f"{major}.{minor}.{sys.version_info.micro}"
    if (major, minor) != (3, 12):
        return CheckResult(
            "Python",
            CheckLevel.WARN,
            f"Python {ver} (recomendado 3.12)",
            detail=sys.executable,
        )
    return CheckResult("Python", CheckLevel.OK, f"Python {ver}", detail=sys.executable)


def _check_deps() -> CheckResult:
    required = ["yaml", "pydantic", "httpx", "structlog", "numpy"]
    missing: list[str] = []
    for mod in required:
        try:
            __import__(mod if mod != "yaml" else "yaml")
        except ImportError:
            missing.append(mod)
    if missing:
        return CheckResult(
            "Dependencias",
            CheckLevel.FAIL,
            f"Faltan: {', '.join(missing)}",
            detail="Ejecuta: poetry install",
        )
    return CheckResult("Dependencias", CheckLevel.OK, "Núcleo instalado")


def _check_ollama(cfg: JarvisConfig) -> CheckResult:
    try:
        import httpx

        url = cfg.llm.base_url.rstrip("/")
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{url}/api/tags")
            resp.raise_for_status()
            models = [m.get("name", "") for m in resp.json().get("models", [])]
        return CheckResult(
            "Ollama",
            CheckLevel.OK,
            f"Activo ({len(models)} modelos)",
            detail=", ".join(models[:8]) or "(vacío)",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "Ollama",
            CheckLevel.FAIL,
            "No responde",
            detail=str(exc),
        )


def _check_models(cfg: JarvisConfig) -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        import httpx

        url = cfg.llm.base_url.rstrip("/")
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{url}/api/tags")
            resp.raise_for_status()
            names = {m.get("name", "") for m in resp.json().get("models", [])}
            # ollama tags suelen ser "llama3.2:3b" o con :latest
            flat = set(names)
            for n in list(names):
                flat.add(n.split(":")[0])
    except Exception:  # noqa: BLE001
        return [
            CheckResult(
                "Modelos",
                CheckLevel.SKIP,
                "No se pudieron listar (Ollama caído)",
            )
        ]

    def has(model: str) -> bool:
        if model in names:
            return True
        base = model.split(":")[0]
        return any(n == model or n.startswith(base + ":") or n == base for n in names)

    required = [
        ("LLM", cfg.llm.model, True),
        ("Embeddings", cfg.memory.embedding_model, cfg.memory.semantic_enabled),
    ]
    if cfg.vision.enabled:
        required.append(("Vision", cfg.vision.model, False))

    for label, model, critical in required:
        if has(model):
            results.append(
                CheckResult(f"Modelo {label}", CheckLevel.OK, model)
            )
        else:
            level = CheckLevel.FAIL if critical else CheckLevel.WARN
            results.append(
                CheckResult(
                    f"Modelo {label}",
                    level,
                    f"Missing model: {model}",
                    detail=f"ollama pull {model}",
                )
            )
    return results


def _check_db(cfg: JarvisConfig) -> CheckResult:
    root = project_root()
    path = root / cfg.memory.db_path
    if not path.exists():
        return CheckResult(
            "Memory DB",
            CheckLevel.WARN,
            "Aún no creada (se crea al primer uso)",
            detail=str(path),
        )
    try:
        import sqlite3

        conn = sqlite3.connect(path)
        conn.execute("SELECT 1")
        conn.close()
        return CheckResult("Memory DB", CheckLevel.OK, "SQLite OK", detail=str(path))
    except Exception as exc:  # noqa: BLE001
        return CheckResult("Memory DB", CheckLevel.FAIL, "Corrupta o inaccesible", detail=str(exc))


def _check_chroma(cfg: JarvisConfig) -> CheckResult:
    root = project_root()
    mem = root / cfg.memory.chroma_dir
    rag = root / cfg.rag.chroma_dir
    try:
        import chromadb  # noqa: F401

        status = []
        if mem.exists():
            status.append("memory")
        if rag.exists():
            status.append("rag")
        if not status:
            return CheckResult(
                "Chroma",
                CheckLevel.WARN,
                "Sin índices aún",
                detail=f"{mem} | {rag}",
            )
        return CheckResult(
            "Chroma",
            CheckLevel.OK,
            f"Disponible ({', '.join(status)})",
        )
    except ImportError:
        return CheckResult("Chroma", CheckLevel.FAIL, "chromadb no instalado")


def _check_audio() -> CheckResult:
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        inputs = [d for d in devices if d.get("max_input_channels", 0) > 0]
        if not inputs:
            return CheckResult("Audio", CheckLevel.WARN, "Sin dispositivos de entrada")
        return CheckResult(
            "Audio",
            CheckLevel.OK,
            f"{len(inputs)} micrófono(s) detectado(s)",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult("Audio", CheckLevel.WARN, "No se pudo consultar audio", detail=str(exc))


def _check_permissions() -> CheckResult:
    """macOS: solo informa; los permisos TCC no se leen de forma fiable sin TCC.db."""
    if sys.platform != "darwin":
        return CheckResult(
            "Permisos",
            CheckLevel.SKIP,
            f"No aplica checklist macOS en {sys.platform}",
        )
    return CheckResult(
        "Permisos",
        CheckLevel.WARN,
        "Verifica Micrófono, Pantalla, Accesibilidad y Notificaciones en Ajustes",
        detail="System Settings → Privacy & Security",
    )


def _check_disk() -> CheckResult:
    root = project_root()
    free = _disk_free_gb(root)
    if free < 2:
        return CheckResult(
            "Disco",
            CheckLevel.FAIL,
            f"Solo {free:.1f} GB libres",
            detail="Se recomiendan ≥5 GB para modelos",
        )
    if free < 5:
        return CheckResult(
            "Disco",
            CheckLevel.WARN,
            f"{free:.1f} GB libres",
            detail="Recomendado ≥5 GB",
        )
    return CheckResult("Disco", CheckLevel.OK, f"{free:.1f} GB libres")


def _check_gpu() -> CheckResult:
    try:
        import psutil

        # macOS no expone GPU fácil; reportamos RAM y hint Metal
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if sys.platform == "darwin":
            return CheckResult(
                "GPU",
                CheckLevel.OK,
                f"Apple / Metal disponible (RAM {ram_gb:.0f} GB)",
                detail="mlx / Core ML según deps",
            )
        return CheckResult("GPU", CheckLevel.SKIP, f"RAM {ram_gb:.0f} GB")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("GPU", CheckLevel.SKIP, "psutil no disponible", detail=str(exc))


def _check_config(cfg: JarvisConfig) -> CheckResult:
    root = project_root()
    path = root / "config" / "config.yaml"
    if not path.exists():
        return CheckResult("Config", CheckLevel.FAIL, "Falta config/config.yaml")
    return CheckResult(
        "Config",
        CheckLevel.OK,
        f"Usuario={cfg.app.user_name} perfil={getattr(cfg.app, 'performance_profile', 'balanced')}",
    )


def _check_rag(cfg: JarvisConfig) -> CheckResult:
    if not cfg.rag.enabled:
        return CheckResult("RAG", CheckLevel.WARN, "Desactivado en config")
    knowledge = project_root() / cfg.rag.knowledge_dir
    if not knowledge.exists():
        return CheckResult(
            "RAG",
            CheckLevel.WARN,
            f"Carpeta knowledge ausente: {knowledge}",
        )
    files = list(knowledge.rglob("*"))
    n = sum(1 for f in files if f.is_file())
    return CheckResult("RAG", CheckLevel.OK, f"Activo ({n} archivos en knowledge/)")


def _check_vision(cfg: JarvisConfig) -> CheckResult:
    if not cfg.vision.enabled:
        return CheckResult("Vision", CheckLevel.SKIP, "Desactivada")
    ocr = cfg.vision.ocr_provider
    if ocr == "tesseract":
        if shutil.which("tesseract"):
            return CheckResult("Vision", CheckLevel.OK, f"OCR={ocr} · VLM={cfg.vision.model}")
        return CheckResult(
            "Vision",
            CheckLevel.WARN,
            "tesseract no está en PATH",
            detail="brew install tesseract tesseract-lang",
        )
    return CheckResult("Vision", CheckLevel.OK, f"OCR={ocr} · VLM={cfg.vision.model}")


def run_doctor(cfg: JarvisConfig) -> DoctorReport:
    report = DoctorReport(product=PRODUCT_NAME, version=read_version_file())
    report.checks.append(_check_config(cfg))
    report.checks.append(_check_python())
    report.checks.append(_check_deps())
    report.checks.append(_check_ollama(cfg))
    report.checks.extend(_check_models(cfg))
    report.checks.append(_check_db(cfg))
    report.checks.append(_check_chroma(cfg))
    report.checks.append(_check_rag(cfg))
    report.checks.append(_check_vision(cfg))
    report.checks.append(_check_audio())
    report.checks.append(_check_permissions())
    report.checks.append(_check_disk())
    report.checks.append(_check_gpu())
    return report


def format_report(report: DoctorReport) -> str:
    symbols = {
        CheckLevel.OK: "✓",
        CheckLevel.WARN: "⚠",
        CheckLevel.FAIL: "✗",
        CheckLevel.SKIP: "·",
    }
    lines = [
        f"{report.product} doctor — v{report.version}",
        "",
    ]
    for c in report.checks:
        sym = symbols[c.level]
        line = f"{sym} {c.name}: {c.message}"
        lines.append(line)
        if c.detail and c.level in (CheckLevel.WARN, CheckLevel.FAIL):
            lines.append(f"    → {c.detail}")
    lines.append("")
    lines.append(
        f"Resumen: {report.ok_count} ok · {report.warn_count} warn · {report.fail_count} fail"
    )
    return "\n".join(lines)


def report_as_dict(report: DoctorReport) -> dict[str, Any]:
    return {
        "product": report.product,
        "version": report.version,
        "ok": report.ok_count,
        "warn": report.warn_count,
        "fail": report.fail_count,
        "checks": [
            {
                "name": c.name,
                "level": c.level.value,
                "message": c.message,
                "detail": c.detail,
            }
            for c in report.checks
        ],
    }
