# Fase 9 completada — Release Candidate / Producción

**Fecha:** 2026-07-27  
**Estado:** Completa (candidato **1.0.0-rc.1**)  
**Producto:** Jarvis

## Entregado

| Área | Implementación |
|------|----------------|
| Versionado | `VERSION`, `CHANGELOG.md`, `RELEASE_NOTES.md`, semver |
| Doctor | `jarvis doctor` (+ `--json`) |
| Perfiles | performance / balanced / lightweight · `jarvis profile` |
| Onboarding | `jarvis onboard` + prompt GUI primer arranque |
| Privacidad | export / wipe / mode + comando de voz |
| Instaladores | `create_app_bundle.sh` mejorado + `create_dmg.sh` |
| Checklist Mac limpio | `docs/CLEAN_MAC_CHECKLIST.md` |
| Reporte | `docs/RELEASE_REPORT.md` |
| GUI | pestaña Release (perfiles, doctor, privacidad) |

## CLI nueva

```bash
poetry run jarvis --version          # 1.0.0-rc.1
poetry run jarvis doctor
poetry run jarvis profile list
poetry run jarvis profile apply lightweight
poetry run jarvis onboard --non-interactive
poetry run jarvis privacy export
poetry run jarvis privacy wipe --yes --keep-name
poetry run jarvis privacy mode on
```

## Distribución

```bash
./scripts/create_app_bundle.sh ~/Applications/Jarvis.app
./scripts/create_dmg.sh          # → dist/Jarvis-1.0.0-rc.1.dmg
```

## Criterios RC

- [x] Versionado semántico y notas
- [x] Onboarding
- [x] Doctor / perfiles / privacidad
- [x] Instalador `.app` + `.dmg` (no firmado)
- [x] Documentación de release
- [ ] Validación en Mac limpio (manual — checklist)

## Siguiente paso

Completar `CLEAN_MAC_CHECKLIST.md` → promover a **1.0.0**.  
Fase 10 (multiagente) solo después del cierre de 1.0.0.
