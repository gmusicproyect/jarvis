"""Tests unitarios de skills Fase 3."""

from __future__ import annotations

from pathlib import Path

from jarvis.skills.base import RiskLevel, SkillContext
from jarvis.skills.builtin.calculator import CalculatorSkill
from jarvis.skills.builtin.datetime_skill import DateTimeSkill
from jarvis.skills.builtin.open_url import OpenUrlSkill
from jarvis.skills.builtin.reminder import ReminderSkill
from jarvis.skills.builtin.timer import TimerSkill
from jarvis.skills.builtin.delete_file import DeleteFileSkill
from jarvis.skills.builtin.read_text import ReadTextFileSkill
from jarvis.skills.builtin.search_files import SearchFilesSkill
from jarvis.skills.builtin.weather import WeatherSkill
from jarvis.skills.builtin.news import NewsSkill
from jarvis.memory.service import MemoryService
from jarvis.memory.session import WindowSessionMemory
from jarvis.memory.sqlite_store import SQLitePersistentMemory


def test_datetime_skill() -> None:
    s = DateTimeSkill()
    assert s.can_handle("¿Qué hora es?") > 0.5
    r = s.execute(SkillContext(user_text="qué hora es"))
    assert r.success
    assert "Son las" in r.message


def test_calculator_skill() -> None:
    s = CalculatorSkill()
    assert s.can_handle("calcula 12 + 5") > 0.5
    r = s.execute(SkillContext(user_text="calcula 12 + 5"))
    assert r.success
    assert "17" in r.message


def test_open_url_detects() -> None:
    s = OpenUrlSkill()
    assert s.can_handle("Abre https://openai.com") > 0.9


def test_open_app_spotify() -> None:
    from jarvis.skills.builtin.open_application import OpenApplicationSkill

    s = OpenApplicationSkill()
    assert s.can_handle("Abre Spotify") > 0.8


def test_timer_skill() -> None:
    s = TimerSkill()
    assert s.can_handle("Pon un temporizador de 10 minutos") > 0.5
    r = s.execute(SkillContext(user_text="Pon un temporizador de 1 minutos"))
    assert r.success
    assert r.data.get("minutes") == 1


def test_reminder_skill(tmp_path: Path) -> None:
    mem = MemoryService(
        WindowSessionMemory(4),
        SQLitePersistentMemory(tmp_path / "r.db"),
        None,
    )
    s = ReminderSkill()
    assert s.can_handle("Recuérdame llamar a Carlos mañana") > 0.5
    r = s.execute(
        SkillContext(user_text="Recuérdame llamar a Carlos mañana", memory=mem)
    )
    assert r.success
    notes = mem.persistent.list_items()
    assert any("Carlos" in i.content for i in notes)


def test_delete_requires_confirm_level() -> None:
    assert DeleteFileSkill.required_permissions == RiskLevel.CONFIRM


def test_read_text_file(tmp_path: Path) -> None:
    f = tmp_path / "hola.txt"
    f.write_text("hola jarvis", encoding="utf-8")
    s = ReadTextFileSkill()
    r = s.execute(SkillContext(user_text=f"Lee el archivo {f}"))
    assert r.success
    assert "hola jarvis" in r.message


def test_search_can_handle() -> None:
    assert SearchFilesSkill().can_handle("Busca el archivo presupuesto.pdf") > 0.5


def test_weather_and_news_can_handle() -> None:
    assert WeatherSkill().can_handle("¿Qué clima hace?") > 0.5
    assert NewsSkill().can_handle("Dame las noticias") > 0.5
