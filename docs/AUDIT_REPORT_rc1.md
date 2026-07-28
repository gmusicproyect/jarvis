# Informe de auditoría — Jarvis 1.0.0-rc.1

Fuente: evaluación externa (Claude) + evidencia local del bundle.  
Fecha de registro en repo: 2026-07-27  
Versión auditada: **1.0.0-rc.1**

Estado inmutable al cierre de este informe:

```
CLEAN_MAC_CHECKLIST: PENDING
tag v1.0.0: BLOCKED
Phase 10: BLOCKED
```

---

## 1. Veredicto

**No listo para iniciar la validación en Mac limpio, y por tanto no listo para 1.0.0.** El producto funciona: 74/74 tests unitarios en verde, `doctor` con 0 fallos, RC generado y todos los subsistemas del camino crítico respondiendo. Pero hay dos bloqueadores que invalidan la validación *antes* de que la ejecutes. El primero: el código fuente no está bajo control de versiones — `src/`, `docs/` y `VERSION` aparecen como untracked y no existe ninguna tag. Eso significa que el DMG de 554K en `dist/` no corresponde a ningún commit, que el PASS de la validación automatizada no está anclado a nada reproducible, y que un `git clean -fd` mal ejecutado borra las nueve fases. El segundo: `--health` reporta `Vision on (llava+tesseract)` mientras `doctor` reporta ambos ausentes en la misma máquina; en un Mac limpio ese indicador te dirá "verde" sobre un subsistema muerto, y el paso "probar visión" del checklist quedaría validado contra un semáforo que miente. Corriges esos dos, regeneras el DMG desde el commit, y entonces la validación manual sí tiene sentido.

### Corrección factual (Cursor)

**P0-1 no es `.gitignore` excluyendo `src/`.** `git check-ignore` no marca `src/`, `docs/` ni `VERSION`. Están **untracked** porque nunca se hizo el commit de las Fases 0–9 (el repo solo tiene commits iniciales + contexto offline). La acción correcta sigue siendo: backup + commit de release sin tocar `VERSION` ni crear tag.

---

## 2. Mapa organizado del proyecto

| Área | Estado según evidencia | Confirmado por |
|---|---|---|
| `config` / `profiles` | Activo | `Usuario=Juan perfil=balanced` |
| `models` / LLM | Activo | Ollama, llama3.2:3b |
| `rag` | Activo | 2 archivos en `knowledge/`, Chroma |
| `memory` | Activo | Memory DB OK + Chroma memory |
| `audio` (wake/STT/TTS) | Activo | 3 micrófonos, kokoro/em_santa, openwakeword/hey_jarvis |
| `gui` | Activo | GUI qt |
| `doctor` | Activo | 15 chequeos ejecutados |
| `automation` | Declarado on | `--health`; sin prueba funcional en el mínimo |
| `vision` | **Declarado on, degradado** | llava ausente + tesseract fuera de PATH |
| `skills`, `plugins` | Activos (código + CLI) | no en extracto mínimo; sí en bundle completo |
| `hardening`, `security`, `privacy` | Activos (código + CLI) | bundle / Fase 8–9 |
| `onboarding`, `backup` | Activos | Fase 9 / release_validate |
| `platform` | Activo | autostart |

Legacy: `legacy/` + scripts viejos movidos; `CONTEXTO-JARVIS.md` histórico (menciona `jarvis_pro.py`).

---

## 3. Resultados reales de comandos

| Comando | Resultado |
|---|---|
| `cat VERSION` | `1.0.0-rc.1` |
| `jarvis --version` | `1.0.0-rc.1` |
| `jarvis doctor` | **12 ok · 3 warn · 0 fail** |
| `jarvis --health` | OK (antes mentía sobre visión; corregido post-auditoría) |
| `pytest tests/unit/` | **74 passed** |
| `dist/` | `Jarvis-1.0.0-rc.1.dmg` (~554K) — bootstrap, no runtime autocontenido |
| `git` | untracked masivo; **tags: ninguna** |

Warnings doctor: `llava` ausente, `tesseract` fuera de PATH, permisos macOS.

---

## 4. Hallazgos

| ID | Sev. | Evidencia | Recomendación | Estado |
|---|---|---|---|---|
| **P0-1** | Bloquea | `src/`, `docs/`, `VERSION` untracked; sin tags | Backup + commit de release **sin** cambiar VERSION ni crear tag | **Cerrado** en `2f4fb71` (docs hash en `949c207`) |
| **P0-2** | Bloquea | `--health` vs `doctor` en visión | `--health` debe sondar estado real | **Corregido** — 75 tests |
| **P0-3** | Bloquea | `Install.command` → `mkdir .../.runtime: Read-only file system` en DMG | Instalar a App Support si origen es `/Volumes` o RO | **Corregido** — `bbffcb3` |
| **P0-4** | Bloquea | `.app` sin `python.path` / `kLSNoExecutableErr` | Pin App Support + launcher bash + xattr | **Corregido** — `2b1ea98` |
| **P0-5** | Bloquea | `ResilientTTS.speak(..., cancel_flag=)` → TypeError; sin respuesta hablada | Aceptar y reenviar `cancel_flag` | **Corregido** — `3fdb8f9` |
| **P1-1** | Antes/tras 1.0.0 | llava/tesseract faltan en dev | Provisionar o declarar visión opcional en onboarding/checklist | **Decidido: visión opt-in para 1.0.0** (`Vision: degraded` = PASS base) |
| **P1-2** | Antes/tras 1.0.0 | DMG bootstrap | Documentar red/descargas en checklist | Documentado; sha256 del artefacto en log |
| **P1-3** | Antes/tras 1.0.0 | solo unit / cov 49% | cov + smoke E2E voz | **Parcial / permanece abierto tras PASS.** 49% unit; huecos en audio/automation/vision/gui/platform. |
| **P1-4** | Antes/tras 1.0.0 | PASS sin hash de commit | Tras commit: re-validar y registrar hash | **Cerrado** — anclas por artefacto |
| **P1-5** | Antes/tras 1.0.0 | Camino B: Ollama/Homebrew a nivel sistema ya presentes | Cold-start del instalador (Install.command sin Ollama/brew) no se verifica | **ABIERTO tras un PASS por Camino B.** Cierre: máquina sin Ollama ni Homebrew. Post-1.0.0. |
| **P1-A** | Antes release público | `create_dmg.sh` horneaba `Jarvis.app` + symlink Applications con rutas de build | Quitar `.app`/symlink del DMG; solo Install.command | **Corregido** en este ciclo — validar en próximo DMG |
| **P1-B** | Verificar en sesión | wake `preds.get("hey_jarvis", 0.0)` si la clave no coincide → score 0 | Confirmar “Hey Jarvis” activa (no solo aplauso) | **ABIERTO — verificar en instalación fresca** |
| **P2-1** | Posterior | warnings pydantic/chromadb | Limpiar post-release | Abierto |
| **P2-2** | Posterior | mensaje llava en inglés | i18n doctor | Abierto |
| **P2-3** | Posterior | llama3.2:3b techo | perfil con modelo mayor opcional | Abierto / Fase futura |

Fuera de alcance: Fase 10, nube cloud, tag `v1.0.0`.

---

## 5. Documentos a actualizar

- `docs/RELEASE_VALIDATION_LOG.md` — hash + cov tras commit
- `docs/CLEAN_MAC_CHECKLIST.md` — red, visión opcional/precondición
- `RELEASE_NOTES.md` — offline runtime vs instalación; visión
- `docs/RELEASE_REPORT.md` — P0 y resolución
- `CONTEXTO-JARVIS.md` — marcar histórico

---

## 6. Hito pendiente único

`CLEAN_MAC_CHECKLIST.md` → **PENDING**. Solo el operador humano marca PASS tras Mac limpio real. No marcar PASS con P0-2 sin corregir (ya corregido en código; falta commit + regen DMG).

---

## 7. Recomendación inmediata

1. Backup + **commit de release** (aprobación del usuario), VERSION sigue `1.0.0-rc.1`, sin tag.
2. Confirmar `--health` degradado cuando falte visión (hecho).
3. Regenerar DMG + `release_validate.sh` con hash de commit → entonces sí Mac limpio.

Sin Fase 10. Sin tag `v1.0.0`.
