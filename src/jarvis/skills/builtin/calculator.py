"""Calculadora básica."""

from __future__ import annotations

import ast
import operator
import re
from typing import Any, ClassVar

from jarvis.skills.base import RiskLevel, SkillContext, SkillResult
from jarvis.skills.builtin._text import score_keywords
from jarvis.skills.skill import Skill

_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op = _OPS[type(node.op)]
        return float(op(_eval_node(node.left), _eval_node(node.right)))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return float(-_eval_node(node.operand))
    raise ValueError("expresión no permitida")


class CalculatorSkill(Skill):
    name: ClassVar[str] = "calculator"
    description: ClassVar[str] = "Evalúa cálculos matemáticos simples"
    aliases: ClassVar[list[str]] = ["calcula", "cuánto es", "cuanto es", "suma", "resta"]
    required_permissions: ClassVar[RiskLevel] = RiskLevel.SAFE

    def can_handle(self, text: str) -> float:
        if re.search(r"\d+\s*[\+\-\*/x×]\s*\d+", text):
            return 0.95
        return score_keywords(
            text, ["calcula", "cuanto es", "cuánto es", "resultado de"], boost=0.88
        )

    def execute(self, ctx: SkillContext) -> SkillResult:
        expr = ctx.user_text.lower()
        expr = re.sub(r".*?(?:calcula|cuanto es|cuánto es|resultado de)\s*", "", expr)
        expr = (
            expr.replace("x", "*")
            .replace("×", "*")
            .replace("÷", "/")
            .replace(",", ".")
        )
        expr = re.sub(r"[^0-9\.\+\-\*/\(\)\s]", "", expr).strip()
        if not expr:
            return SkillResult(False, "No entendí la operación.")
        try:
            tree = ast.parse(expr, mode="eval")
            value = _eval_node(tree)
            if value == int(value):
                value = int(value)
            return SkillResult(True, f"El resultado es {value}.", data={"value": value})
        except Exception as exc:  # noqa: BLE001
            return SkillResult(False, "No pude calcular eso.", error=str(exc))
