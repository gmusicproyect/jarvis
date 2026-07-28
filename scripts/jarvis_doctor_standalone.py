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


def prefer_python() -> list[str]:
    """Usa el Python del venv de Jarvis / Poetry si existe (no el system bare)."""
    candidates = [
        HOME / "Library/Application Support/Jarvis/venv/bin/python",
        ROOT / ".runtime" / "venv" / "bin" / "python",
        ROOT / ".venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return [str(c)]
    # poetry
    if shutil.which("poetry") and (ROOT / "pyproject.toml").is_file():
        try:
            proc = subprocess.run(
                ["poetry", "env", "info", "-p"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            env_p = (proc.stdout or "").strip()
            py = Path(env_p) / "bin" / "python"
            if py.is_file():
                return [str(py)]
        except Exception:  # noqa: BLE001
            pass
    return [sys.executable]


def reexec_in_project_python() -> None:
    """Si este intérprete no tiene deps de voz, reintenta con el venv del proyecto."""
    if os.environ.get("JARVIS_DOCTOR_REEXEC") == "1":
        return
    try:
        import faster_whisper  # noqa: F401
        import sounddevice  # noqa: F401
        return
    except ImportError:
        pass
    target = prefer_python()
    if Path(target[0]).resolve() == Path(sys.executable).resolve():
        return
    os.environ["JARVIS_DOCTOR_REEXEC"] = "1"
    os.execv(target[0], [*target, str(Path(__file__).resolve()), *sys.argv[1:]])


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

    # Micrófono (1s) — crítico en Mac limpio real; sin dispositivo = WARN (CI/sandbox)
    print("...probando micrófono 1s...")
    try:
        import numpy as np
        import sounddevice as sd

        devices = sd.query_devices()
        inputs = [d for d in devices if d.get("max_input_channels", 0) > 0]
        if not inputs:
            check(
                "Micrófono capta señal",
                False,
                "sin dispositivos de entrada (CI/sandbox?)",
                critical=False,
            )
        else:
            audio = sd.rec(int(1.0 * 16000), samplerate=16000, channels=1, dtype="float32")
            sd.wait()
            nivel = float(np.abs(audio).max())
            check("Micrófono capta señal", nivel > 0.0005, f"nivel={nivel:.5f}")
    except Exception as exc:  # noqa: BLE001
        check("Micrófono capta señal", False, str(exc), critical=False)

    # CLI jarvis si está en PATH / venv / poetry
    jarvis_bin = shutil.which("jarvis")
    venv_jarvis = HOME / "Library/Application Support/Jarvis/venv/bin/jarvis"
    poetry_jarvis: list[str] | None = None
    if shutil.which("poetry") and (ROOT / "pyproject.toml").is_file():
        poetry_jarvis = ["poetry", "run", "jarvis"]

    if jarvis_bin or venv_jarvis.is_file() or poetry_jarvis:
        if jarvis_bin:
            cmd = [jarvis_bin]
        elif venv_jarvis.is_file():
            cmd = [str(venv_jarvis)]
        else:
            cmd = poetry_jarvis  # type: ignore[assignment]
        try:
            proc = subprocess.run(
                [*cmd, "--health"],
                cwd=ROOT,
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
                next(
                    (
                        ln.strip()
                        for ln in out.splitlines()
                        if ln.strip().startswith("Jarvis ")
                    ),
                    f"rc={proc.returncode}",
                )[:80],
            )
            check(
                "jarvis --health no miente (P0-2)",
                not lying,
                "Vision: on sin llava" if lying else "ok",
            )
            check(
                "Vision degraded/off esperado sin llava",
                degraded_ok or has_llava,
                next(
                    (
                        ln.strip()
                        for ln in out.splitlines()
                        if "Vision:" in ln
                    ),
                    "sin línea Vision",
                )[:100],
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
        reexec_in_project_python()
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"ERROR de red: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
