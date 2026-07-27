# Release validation log

## Ancla de c�digo (P0-1 cerrado)

| Campo | Valor |
|-------|--------|
| Commit | `2f4fb71` (`2f4fb711e0a3849c132bf41ce44c2fb4608376ca`) |
| Mensaje | chore(release): anclar �rbol de Fases 0-9 en 1.0.0-rc.1 |
| VERSION | 1.0.0-rc.1 (sin cambio) |
| Tags | ninguna |
| Unit tests post P0-2 | **75 passed** |
| `--health` Vision | `degraded` cuando faltan llava/tesseract |

Re-ejecutar `./scripts/release_validate.sh` y regenerar DMG **desde este hash** antes del Mac limpio.

---

| Campo | Valor |
|-------|--------|
| Fecha UTC | 2026-07-27T22:11:13Z |
| Versi�n | 1.0.0-rc.1 |
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
| PASS | backup-create | /Users/juanlizamah/jarvis/data/backups/jarvis-backup-20260727-181117-release-validate.zip |
| PASS | happy:hora | Jarvis: Son las 18:11 del lunes 27 de julio de 2026. |
| PASS | happy:memoria | Jarvis: Queda anotado en mi memoria. |
| PASS | happy:rag | Jarvis: ¿Qué archivo o carpeta busco? |
| PASS | happy:app | Jarvis: No pude calcular eso. |
| PASS | happy:screenshot | Jarvis: Captura guardada en /Users/juanlizamah/jarvis/data/screenshots/jarvis-shot-20260727-181207.png. |
| PASS | happy:vision | respuesta recibida |
| PASS | privacy-export | /Users/juanlizamah/jarvis/data/exports/jarvis-export-20260727-221238.json |
| PASS | privacy-wipe | items 4 → 0 |
| PASS | backup-restore | memoria tras restore=3 (antes wipe=4) |
| PASS | snapshot-after-restore | config/plugins/chroma presentes |
| PASS | resolve-python | /var/folders/wh/1zszv0hs2d3d9syy8fc9rncr0000gn/T/cursor-sandbox-cache/ad65f122330af5bea7df0e33b0c7ebca/poetry/virtualenvs/jarvis-bEVZkWHD-py3.12/bin/python |
| PASS | unit-tests |  |
| PASS | dmg-artifact | dist/Jarvis-1.0.0-rc.1.dmg |

## Doctor (extracto)

```
[1mHTTP Request: GET http://127.0.0.1:11434/api/tags "HTTP/1.1 200 OK"[0m
[1mHTTP Request: GET http://127.0.0.1:11434/api/tags "HTTP/1.1 200 OK"[0m
Jarvis doctor — v1.0.0-rc.1

✓ Config: Usuario=Juan perfil=balanced
✓ Python: Python 3.12.13
✓ Dependencias: Núcleo instalado
✓ Ollama: Activo (2 modelos)
✓ Modelo LLM: llama3.2:3b
✓ Modelo Embeddings: nomic-embed-text
⚠ Modelo Vision: Missing model: llava
    → ollama pull llava
✓ Memory DB: SQLite OK
✓ Chroma: Disponible (memory, rag)
✓ RAG: Activo (2 archivos en knowledge/)
⚠ Vision: tesseract no está en PATH
    → brew install tesseract tesseract-lang
✓ Audio: 3 micrófono(s) detectado(s)
⚠ Permisos: Verifica Micrófono, Pantalla, Accesibilidad y Notificaciones en Ajustes
    → System Settings → Privacy & Security
✓ Disco: 56.1 GB libres
✓ GPU: Apple / Metal disponible (RAM 18 GB)

Resumen: 12 ok · 3 warn · 0 fail
```

## Mac limpio / firma

- Mac limpio manual: **PENDIENTE** (ver CLEAN_MAC_CHECKLIST.md)
- Firma/notarización: **PENDIENTE** salvo `JARVIS_CODESIGN_ID`
- Promoción a 1.0.0: **BLOQUEADA** mientras FAIL>0 o Mac limpio ≠ PASS

**Veredicto automatizado:** READY_FOR_CLEAN_MAC (no es PASS de release todavía).
