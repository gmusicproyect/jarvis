# Seguridad Jarvis

## Principios

- Local-first: el camino crítico no requiere cloud.
- Permisos por niveles (SAFE / CONFIRM / RESTRICTED).
- Confirmación por voz antes de acciones sensibles.
- Auditoría de automatización y seguridad.

## Secret Manager

No guardes API keys en `config.yaml`.

```python
from jarvis.security import SecretManager
sm = SecretManager()
sm.set("openai_api_key", "…")   # macOS Keychain / env
print(sm.get("openai_api_key"))
```

- macOS → Keychain (`security` CLI)
- Windows → stub Credential Manager (fallback env)
- Linux → variables de entorno

## Auditoría

- Automatización: `data/db/automation_audit.db`
- Seguridad unificada: `data/db/security_audit.db` (vía `SecurityAudit`)

Cada registro incluye usuario, acción, skill, permiso y resultado.

## Shell

Solo comandos en `automation.shell_allowlist`. Comandos peligrosos (`rm`, `sudo`, …) son RESTRICTED.

## Privacidad (Fase 9)

```bash
poetry run jarvis privacy export          # JSON en data/exports/
poetry run jarvis privacy wipe --yes      # borra memoria personal
poetry run jarvis privacy mode on         # menos retención / logs
```

Por voz: *«elimina todo lo que recuerdas de mí»*.

El modo privacidad reduce `short_term_turns`, desactiva memoria semántica y sube el nivel de log a WARNING.
