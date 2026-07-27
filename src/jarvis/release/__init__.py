"""Release metadata — nombre de producto y versión."""

from __future__ import annotations

from pathlib import Path

PRODUCT_NAME = "Jarvis"
PRODUCT_BUNDLE_ID = "com.jarvis.assistant"


def read_version_file() -> str:
    """Lee VERSION en la raíz del proyecto; fallback a metadata del paquete."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8").strip()
            if text:
                return text
        if (parent / "pyproject.toml").is_file() and (parent / "config").is_dir():
            break
    try:
        from jarvis import __version__ as pkg_version

        return pkg_version
    except Exception:  # noqa: BLE001
        return "1.0.0-rc.1"
