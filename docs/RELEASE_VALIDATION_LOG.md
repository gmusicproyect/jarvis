# Release validation log

## Artefacto anclado (build post P1-1)

```text
Artefacto:     dist/Jarvis-1.0.0-rc.1.dmg (612K)
Commit ancla:  741dd82 (741dd825567f17deb1a76d7dc9837b86fc12d24e)
Ancla previa:  d045037 — superada por decisión visión opt-in (P1-1)
Cadena:        d045037 ? 741dd82 (1 commit docs; merge-base ancestor OK)
Árbol:         limpio en el momento del build (docs visión opt-in incluidos)
SHA-256:       aebebe2478f51b105f94cd005d3b5c486f68829520f2a3069498357819d7e57c
Huella local:  ~/Desktop/jarvis_rc1_dmg.sha256
Tests:         75 passed — tests/unit/
Cobertura:     49% lineas (TOTAL 6598/3108 miss) — unit only; P1-3 PARCIAL y permanece abierto tras PASS
Doctor:        12 ok · 3 warn · 0 fail (llava, tesseract, permisos macOS)
Health:        Vision: degraded — reporta runtime real (P0-2 cerrado)
Vision 1.0.0:  OPT-IN — degraded = PASS del camino base (P1-1 cerrado)
release_validate.sh: PASS (17 PASS / 1 WARN / 0 FAIL)
Mac limpio:    Camino B — instalación fresca de Jarvis (preferir cuenta nueva)
               PENDING — inventario sistema ? "Alcance del PASS"; P1-5 ABIERTO si Ollama/brew preexistentes
P1-5:          Cold-start instalador no verificado bajo Camino B — ABIERTO post-PASS
Tag v1.0.0:    no creada — bloqueada
Fase 10:       bloqueada
```

Log crudo de validación: `~/Desktop/release_validate_741dd82.log`

---

| Campo | Valor |
|-------|--------|
| Fecha UTC | 2026-07-28T00:13:07Z |
| Versión | 1.0.0-rc.1 |
| PASS | 17 |
| WARN | 1 |
| FAIL | 0 |

## Resultados

| Estado | Check | Detalle |
|--------|-------|---------|
| PASS | version | 1.0.0-rc.1 |
| WARN | doctor | advertencias (exit 1) — ver salida |
| PASS | doctor-no-critical | sin fallos críticos |
| PASS | snapshot-before | capturado |
| PASS | backup-create | data/backups/…-release-validate.zip |
| PASS | happy:hora | respuesta hablable |
| PASS | happy:memoria | recuerdo guardado |
| PASS | happy:rag | respuesta con contexto de knowledge/ |
| PASS | happy:app | intento open_application (TextEdit; wording frágil) |
| PASS | happy:screenshot | captura guardada |
| PASS | happy:vision | respuesta recibida (degraded OK) |
| PASS | privacy-export | JSON exportado |
| PASS | privacy-wipe | items ? 0 |
| PASS | backup-restore | memoria restaurada |
| PASS | snapshot-after-restore | config/plugins/chroma presentes |
| PASS | resolve-python | intérprete con jarvis |
| PASS | unit-tests | 75 passed |
| PASS | dmg-artifact | dist/Jarvis-1.0.0-rc.1.dmg |

## Doctor (extracto)

```
? Config / Python 3.12 / Dependencias / Ollama
? LLM llama3.2:3b / Embeddings nomic-embed-text
? Missing model: llava
? tesseract no está en PATH
? Permisos macOS (checklist manual)
Resumen: 12 ok · 3 warn · 0 fail
```

## Mac limpio / firma

- Mac limpio manual: **PENDING** (`docs/CLEAN_MAC_CHECKLIST.md`)
- Firma/notarización: PENDING salvo `JARVIS_CODESIGN_ID`
- Promoción a 1.0.0: **BLOQUEADA** hasta PASS del checklist

**Veredicto automatizado:** READY_FOR_CLEAN_MAC (no es PASS de release todavía).
