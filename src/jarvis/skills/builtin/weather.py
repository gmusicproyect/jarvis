"""Clima vía Open-Meteo (sin API key) u otro provider en config."""

from __future__ import annotations

from typing import ClassVar

import httpx

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill


class WeatherSkill(Skill):
    name: ClassVar[str] = "weather"
    description: ClassVar[str] = "Consulta el clima actual"
    aliases: ClassVar[list[str]] = ["clima", "tiempo", "temperatura", "hará frío"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(
            text, ["clima", "temperatura", "hace frio", "hace calor", "el tiempo"], boost=0.92
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        cfg = ctx.config.get("weather", {})
        provider = cfg.get("provider", "open_meteo")
        lat = float(cfg.get("latitude", 9.93))
        lon = float(cfg.get("longitude", -84.08))
        city = cfg.get("city", "San José")

        if provider != "open_meteo":
            return SkillResult(
                False,
                f"Proveedor de clima '{provider}' no implementado. Usa open_meteo.",
            )
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
            )
            with httpx.Client(timeout=20.0) as client:
                data = client.get(url).json()
            temp = data.get("current", {}).get("temperature_2m")
            if temp is None:
                return SkillResult(False, "No obtuve datos del clima.")
            return SkillResult(
                True,
                f"En {city} hay aproximadamente {temp} grados Celsius.",
                data={"temp_c": temp, "city": city},
            )
        except Exception as exc:  # noqa: BLE001
            return SkillResult(
                False,
                "No pude consultar el clima ahora.",
                error=str(exc),
            )
