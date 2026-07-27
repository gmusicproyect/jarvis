"""Hardening — errores y recuperación."""

from jarvis.hardening.errors import ErrorHandler, FailureRecord, get_error_handler
from jarvis.hardening.recovery import OllamaHealth, ResilientTTS, register_default_recoveries

__all__ = [
    "ErrorHandler",
    "FailureRecord",
    "OllamaHealth",
    "ResilientTTS",
    "get_error_handler",
    "register_default_recoveries",
]
