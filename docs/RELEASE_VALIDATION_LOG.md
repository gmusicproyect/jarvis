# Release validation log

## Artefacto anclado (post P1-A + P0-5 TTS)

```text
Artefacto:     dist/Jarvis-1.0.0-rc.1.dmg (731K)
Commit ancla:  910d3dc (910d3dcbdf080a57a632de28bcdb878a36889418)
Contiene:      P0-3 Install RO · P0-4 .app python.path · P0-5 TTS cancel_flag
               P1-A DMG sin Jarvis.app/Applications horneados
SHA-256:       44ba93a379f076d9f347d8b6ae496528f868d4e19b25d1e2acd787b2b5c16851
Huella local:  ~/Desktop/jarvis_rc1_dmg.sha256
Contenido DMG: Install.command + JarvisSource + LEEME (sin .app arrastrable)
Mac limpio:    PENDING — instalación fresca sobre ESTE artefacto
P1-B:          Verificar que "Hey Jarvis" dispara (no solo aplauso)
P1-2/P1-3/P1-5: ABIERTOS
Tag v1.0.0:    BLOQUEADA
Fase 10:       BLOQUEADA
```

## Anclas superadas (no usar)

| Ancla | SHA-256 (corto) | Motivo |
|-------|-----------------|--------|
| 741dd82 | aebebe24… | Install RO (P0-3) |
| bbffcb3 | b8b42f0f… | .app sin fix completo |
| 2b1ea98 | d1cc8cbc… | sin TTS cancel_flag (P0-5) ni P1-A |

## Gates

- Mac limpio manual: **PENDING** (`docs/CLEAN_MAC_CHECKLIST.md`)
- Firma/notarización: PENDING
- Tag `v1.0.0`: BLOCKED
- Fase 10: BLOCKED
