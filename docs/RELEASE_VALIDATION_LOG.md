# Release validation log

## Artefacto anclado (post P0-3 — Install.command DMG RO)

```text
Artefacto:     dist/Jarvis-1.0.0-rc.1.dmg (728K)
Commit ancla:  bbffcb3 (bbffcb3441cc308d9ca6f8bc228ad1382e930b9d)
Ancla previa:  741dd82 / aebebe24… — FAIL 2026-07-28:
               mkdir Read-only en /Volumes/.../JarvisSource/.runtime (P0-3)
SHA-256:       b8b42f0f492f792d8bd8424be45459977bfe01a6dc0522bcc52cc924955f1763
Huella local:  ~/Desktop/jarvis_rc1_dmg.sha256
Fix:           install_standalone copia a Application Support si origen es DMG/RO
Mac limpio:    PENDING — reintentar con este DMG (eject volumen viejo primero)
P1-2/P1-3/P1-5: ABIERTOS (P1-5 tras PASS Camino B)
Tag v1.0.0:    no creada — bloqueada
Fase 10:       bloqueada
```

## Sesión FAIL (artefacto anterior)

```text
Fecha:         2026-07-28 ~13:20 local
DMG:           741dd82 / aebebe2478f51b105f94cd005d3b5c486f68829520f2a3069498357819d7e57c
Síntoma:       Install.command ? mkdir: .../JarvisSource/.runtime: Read-only file system
Resultado:     FAIL — no instalar ese DMG; usar bbffcb3 / b8b42f0f…
```

Log crudo de validación automatizada (histórico): `~/Desktop/release_validate_741dd82.log`

---

| Campo | Valor |
|-------|--------|
| Fecha UTC | 2026-07-28T17:22:00Z (rebuild P0-3) |
| Versión | 1.0.0-rc.1 |
| Ancla | bbffcb3 |
| SHA-256 | b8b42f0f492f792d8bd8424be45459977bfe01a6dc0522bcc52cc924955f1763 |

## Resultados

Validación automatizada del ancla previo (`741dd82`) sigue archivada abajo como histórico.
La validación manual debe usar **solo** el DMG `b8b42f0f…`.

### Histórico release_validate (741dd82)

| Estado | Check | Detalle |
|--------|-------|---------|
| PASS | (17 checks) | Ver log crudo en Desktop |
| WARN | 1 | (archivado) |
| FAIL | 0 | |

## Gates

- Mac limpio manual: **PENDING** (`docs/CLEAN_MAC_CHECKLIST.md`) — tarjeta nueva tras P0-3
- Firma/notarización: PENDING salvo `JARVIS_CODESIGN_ID`
- Tag `v1.0.0`: BLOCKED
- Fase 10: BLOCKED
