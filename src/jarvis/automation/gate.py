"""Puerta de permisos por niveles + descripción previa."""

from __future__ import annotations

from jarvis.automation.base import ActionRequest, ActionResult, PermissionLevel
from jarvis.utils.logging import get_logger


class PermissionGate:
    """
    Nivel 1 SAFE → ejecuta.
    Nivel 2 CONFIRM → requiere confirmación explícita.
    Nivel 3 RESTRICTED → bloqueado salvo allow_restricted + confirmación.
    """

    def __init__(
        self,
        *,
        allow_restricted: bool = False,
        confirm_destructive: bool = True,
    ) -> None:
        self.allow_restricted = allow_restricted
        self.confirm_destructive = confirm_destructive
        self._log = get_logger("jarvis.automation.permissions")

    def authorize(
        self, request: ActionRequest, *, confirmed: bool = False
    ) -> ActionResult | None:
        """Devuelve ActionResult de bloqueo, o None si puede continuar."""
        self._log.info(
            "permission_check",
            action=request.action,
            level=request.level.value,
            description=request.description,
            confirmed=confirmed,
        )
        if request.level == PermissionLevel.SAFE:
            return None

        if request.level == PermissionLevel.RESTRICTED:
            if not self.allow_restricted:
                return ActionResult(
                    success=False,
                    message=(
                        f"Acción restringida bloqueada: {request.description}. "
                        "Activa security.allow_restricted en config si es necesario."
                    ),
                    action=request.action,
                    level=request.level,
                    confirmed=False,
                )
            if self.confirm_destructive and not confirmed:
                return ActionResult(
                    success=False,
                    message=(
                        f"Acción restringida: {request.description}. "
                        "Di 'confirma' para proceder o 'cancela' para abortar."
                    ),
                    action=request.action,
                    level=request.level,
                    data={"needs_confirm": True},
                    confirmed=False,
                )
            return None

        # CONFIRM
        if self.confirm_destructive and not confirmed:
            return ActionResult(
                success=False,
                message=(
                    f"Confirmación requerida: {request.description}. "
                    "Di 'confirma' para proceder o 'cancela' para abortar."
                ),
                action=request.action,
                level=request.level,
                data={"needs_confirm": True},
                confirmed=False,
            )
        return None
