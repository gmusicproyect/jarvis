# Release Report — Jarvis 1.0.0-rc.1

| Campo | Valor |
|-------|--------|
| Fecha | 2026-07-27 |
| Producto | Jarvis |
| Versión | 1.0.0-rc.1 |
| Criterio | Release Candidate (pre-1.0.0) |
| Autor del reporte | Automatizado / desarrollo |

## Hardware / SO (estación de desarrollo)

| Ítem | Valor |
|------|--------|
| SO | macOS (darwin) |
| Python | 3.12 (Poetry) |
| LLM local | Ollama |
| Notas | Validación de código + tests unitarios en máquina de desarrollo. **Mac limpio pendiente** — ver `CLEAN_MAC_CHECKLIST.md`. |

## Tests ejecutados

| Suite | Resultado |
|-------|-----------|
| `tests/unit/` | **74 passed** (2026-07-27) |
| `tests/unit/test_fase9.py` | 8 passed |
| `jarvis doctor` | 11 ok · 4 warn · 0 fail (faltan llava/tesseract en estación de build) |
| `jarvis profile list` | OK |
| `jarvis onboard --non-interactive --force` | OK |
| `jarvis privacy export` | OK → `data/exports/` |
| `create_app_bundle.sh` | OK |
| `create_dmg.sh` | OK → `dist/Jarvis-1.0.0-rc.1.dmg` |

## Problemas conocidos

1. DMG / `.app` **sin firma** Apple Developer ID → Gatekeeper requiere «Abrir» manual.
2. El launcher del `.app` apunta al path del repo (no es un bundle Python standalone).
3. Modelos grandes no se incluyen en el instalador (pull vía Ollama).
4. Cobertura ≥90% en críticos: objetivo de 1.0.0; RC cubre módulos nuevos con tests dedicados.

## Criterio de salida RC

| Criterio | Estado |
|----------|--------|
| Instala en Mac limpio | **Criterio aligerado:** instalación fresca (no Mac virgen). PENDING |
| Funciona sin terminal (GUI) | Sí (`jarvis gui` / `.app`) |
| Onboarding inicial | Sí |
| Recuperación ante fallos comunes | Sí (doctor + hardening Fase 8) |
| Backup/restore probado | Sí (smoke) |
| Documentación completa | Sí |
| Instalador distribuible | Sí (DMG no firmado) |

## Notas de cierre RC → 1.0.0 (2026-07-27)

### Auditoría externa (Claude) + acciones Cursor

Ver `docs/AUDIT_REPORT_rc1.md`.

| ID | Acción |
|----|--------|
| P0-1 | Código untracked (no ignorado) — **commit de release pendiente de aprobación** |
| P0-2 | `--health` ahora sonda visión real (`on` / `degraded` / `off`) |

### Hecho en estación de desarrollo
- Validación automatizada: **17 PASS / 1 WARN / 0 FAIL** (`docs/RELEASE_VALIDATION_LOG.md`)
- Happy path sin wake (hora, memoria, RAG, app, screenshot, visión)
- Privacy export (perfil/memoria/prefs/refs docs/config) + wipe + restore
- TTS: fallback a `system` si falta `mlx_audio`
- Launcher `.app` sin Poetry en PATH (`python.path` + `install_standalone_macos.sh`)
- Script firma/notarización: `scripts/codesign_and_notarize.sh`

### Pendiente (bloquea v1.0.0)
- Commit de release anclado (P0-1) + re-validar con hash
- Mac limpio PASS (`docs/CLEAN_MAC_CHECKLIST.md`) — criterio: instalación fresca, no hardware virgen
- Firma + notarización Apple (si distribución pública)
- Tag `v1.0.0` / bump VERSION

**No se promociona a 1.0.0 ni se inicia Fase 10 hasta el PASS del checklist.**

## Comando de verificación rápida

```bash
poetry run jarvis --version
poetry run jarvis doctor
poetry run pytest tests/unit/test_fase9.py -q --no-cov
./scripts/create_app_bundle.sh /tmp/Jarvis.app
```
