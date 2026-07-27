"""Jarvis — asistente de voz personal local-first."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _version_from_file() -> str | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8").strip()
            return text or None
        if (parent / "pyproject.toml").is_file():
            break
    return None


def _resolve_version() -> str:
    file_ver = _version_from_file()
    if file_ver:
        return file_ver
    try:
        return version("jarvis")
    except PackageNotFoundError:  # pragma: no cover
        return "1.0.0-rc.1"


__version__ = _resolve_version()

__all__ = ["__version__"]
