"""Test mínimo del plugin echo."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skill import EchoSkill  # noqa: E402
from jarvis.skills.base import SkillContext  # noqa: E402


def test_echo() -> None:
    s = EchoSkill()
    assert s.can_handle("eco hola") > 0.9
    r = s.execute(SkillContext(user_text="eco hola"))
    assert r.success and r.message == "hola"
