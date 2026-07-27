"""Noticias vía RSS configurable."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import ClassVar

import httpx

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill


class NewsSkill(Skill):
    name: ClassVar[str] = "news"
    description: ClassVar[str] = "Lee titulares de un feed RSS configurable"
    aliases: ClassVar[list[str]] = ["noticias", "titulares", "qué hay de nuevo"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        return score_keywords(text, ["noticias", "titulares", "news"], boost=0.92)

    def execute(self, ctx: SkillContext) -> SkillResult:
        cfg = ctx.config.get("news", {})
        feed = cfg.get(
            "rss_url",
            "https://feeds.bbci.co.uk/mundo/rss.xml",
        )
        limit = int(cfg.get("limit", 3))
        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                xml = client.get(feed).text
            root = ET.fromstring(xml)
            titles: list[str] = []
            for item in root.findall(".//item"):
                title = item.findtext("title")
                if title:
                    titles.append(title.strip())
                if len(titles) >= limit:
                    break
            if not titles:
                return SkillResult(False, "No encontré titulares.")
            joined = "; ".join(titles)
            return SkillResult(
                True,
                f"Titulares: {joined}.",
                data={"titles": titles, "feed": feed},
            )
        except Exception as exc:  # noqa: BLE001
            return SkillResult(False, "No pude obtener noticias.", error=str(exc))
