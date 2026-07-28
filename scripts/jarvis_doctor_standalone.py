#!/usr/bin/env python3
"""JARVIS DOCTOR (standalone) — chequeo PASS/FAIL para sesión Mac limpio.

Alineado con Jarvis 1.0.0-rc.1 (src/jarvis + Ollama local-first).
Visión degradada (sin llava/tesseract) NO es FAIL — es opt-in.

Uso:
  python3 scripts/jarvis_doctor_standalone.py
  # o tras Install.command:
  ~/.local/.../venv/bin/python scripts/jarvis_doctor_standalone.py

Exit 0 = todos los checks críticos PASS.
Exit 1 = hay FAIL crítico.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parents[1]
CRITICAL: list[bool] = []
WARNINGS = 0


def check(nombre: str, ok: bool, detalle: str = "", *, critical: bool = True) -> None:
    global WARNINGS
    if critical:
        CRITICAL.append(ok)
        marca = "PASS" if ok else "FAIL"
    else:
        if not ok:
            WARNINGS += 1
        marca = "PASS" if ok else "WARN"
    extra = f" -> {detalle}" if detalle else ""
    print(f"[{marca}] {nombre}{extra}")


def http_get(url: str, timeout: float = 5.0) -> tuple[bool, object]:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return True, (resp.status, body)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def main() -> int:
    print("=" * 50)
    print("JARVIS DOCTOR (standalone) — 1.0.0-rc.1")
    print("=" * 50)

    # --- núcleo offline ---
    ok, det = http_get("http://127.0.0.1:11434/api/tags")
    check("Ollama responde (127.0.0.1:11434)", ok, str(det if not ok else "200"))

    models: list[str] = []
    if ok and isinstance(det, tuple):
        try:
            payload = json.loads(det[1].decode())
            models = [m.get("name", "") for m in payload.get("models", [])]
        except Exception as exc:  # noqa: BLE001
            check("Parse modelos Ollama", False, str(exc))
            models = []

    has_llm = any("llama3.2" in m for m in models)
    check(
        "Modelo llama3.2 disponible",
        has_llm,
        ", ".join(models) or "ninguno",
    )

    has_embed = any("nomic-embed" in m for m in models)
    check(
        "Modelo nomic-embed-text disponible",
        has_embed,
        ", ".join(models) or "ninguno",
        critical=False,  # WARN: RAG semántico degradado pero sistema usable
    )

    # Visión opt-in: ausencia = WARN, no FAIL
    has_llava = any(m.split(":")[0] == "llava" or m.startswith("llava:") for m in models)
    check(
        "Modelo llava (visión opt-in)",
        has_llava,
        "ausente = Vision degraded OK para 1.0.0 base",
        critical=False,
    )
    tess = shutil.which("tesseract")
    check(
        "tesseract en PATH (visión opt-in)",
        tess is not None,
        tess or "ausente = OK para PASS base",
        critical=False,
    )

    # n8n: opcional en RC (camino crítico = Ollama directo)
    ok_n8n, det_n8n = http_get("http://127.0.0.1:5678")
    check(
        "n8n responde (opcional)",
        ok_n8n,
        str(det_n8n if not ok_n8n else "ok"),
        critical=False,
    )

    # Producto versionado (no legacy jarvis_pro.py)
    check("Existe VERSION", (ROOT / "VERSION").is_file(), str(ROOT / "VERSION"))
    version = ""
    if (ROOT / "VERSION").is_file():
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    check(
        "VERSION es 1.0.0-rc.1",
        version == "1.0.0-rc.1",
        version or "vacío",
    )
    check(
        "Existe src/jarvis/__main__.py",
        (ROOT / "src" / "jarvis" / "__main__.py").is_file(),
        str(ROOT / "src" / "jarvis"),
    )
    check(
        "Existe config/config.yaml",
        (ROOT / "config" / "config.yaml").is_file(),
    )
    check(
        "Sonido ding del sistema",
        Path("/System/Library/Sounds/Ping.aiff").exists(),
        critical=False,
    )

    # Imports de voz
    for modulo, nombre, critical in [
        ("faster_whisper", "Whisper / faster_whisper (STT)", True),
        ("openwakeword", "openwakeword (wake)", True),
        ("mlx_audio", "Kokoro/mlx-audio (TTS)", False),  # fallback system TTS
        ("sounddevice", "sounddevice (audio I/O)", True),
        ("numpy", "numpy", True),
    ]:
        try:
            __import__(modulo)
            check(f"{nombre} instalado", True, critical=critical)
        except Exception as exc:  # noqa: BLE001
            check(f"{nombre} instalado", False, str(exc), critical=critical)

    # Micrófono (1s)
    print("...probando micrófono 1s...")
    try:
        import numpy as np
        import sounddevice as sd

        audio = sd.rec(int(1.0 * 16000), samplerate=16000, channels=1, dtype="float32")
        sd.wait()
        nivel = float(np.abs(audio).max())
        check("Micrófono capta señal", nivel > 0.0005, f"nivel={nivel:.5f}")
    except Exception as exc:  # noqa: BLE001
        check("Micrófono capta señal", False, str(exc))

    # CLI jarvis si está en PATH / venv
    jarvis_bin = shutil.which("jarvis")
    venv_jarvis = HOME / "Library/Application Support/Jarvis/venv/bin/jarvis"
    if jarvis_bin or venv_jarvis.is_file():
        cmd = [jarvis_bin] if jarvis_bin else [str(venv_jarvis)]
        try:
            proc = subprocess.run(
                [*cmd, "--health"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            degraded_ok = "Vision: degraded" in out or "Vision: off" in out
            lying = "Vision: on (" in out and "llava" in out.lower() and not has_llava
            check(
                "jarvis --health ejecuta",
                proc.returncode == 0,
                out.splitlines()[-1][:80] if out else f"rc={proc.returncode}",
            )
            check(
                "jarvis --health no miente (P0-2)",
                not lying,
                "Vision: on sin llava" if lying else "ok",
            )
            check(
                "Vision degraded/off esperado sin llava",
                degraded_ok or has_llava,
                "buscar línea Vision: en --health",
                critical=False,
            )
        except Exception as exc:  # noqa: BLE001
            check("jarvis --health ejecuta", False, str(exc), critical=False)
    else:
        check(
            "jarvis CLI en PATH/venv",
            False,
            "corre tras Install.command",
            critical=False,
        )

    print("=" * 50)
    critical_pass = sum(CRITICAL)
    critical_total = len(CRITICAL)
    all_critical = critical_pass == critical_total
    print(
        f"CRITICOS: {critical_pass}/{critical_total} PASS"
        + (f" · WARN={WARNINGS}" if WARNINGS else "")
    )
    if all_critical:
        print("RESULTADO: SISTEMA SALUDABLE (camino base 1.0.0)")
    else:
        print("RESULTADO: HAY FALLOS CRITICOS ARRIBA")
    print("=" * 50)
    print(
        "Nota: n8n y jarvis_pro.py NO son requisitos del RC. "
        "Visión opt-in: WARN sin llava/tesseract es OK."
    )
    return 0 if all_critical else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"ERROR de red: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
