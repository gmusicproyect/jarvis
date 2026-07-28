# Checklist — Mac limpio (Jarvis 1.0 RC)

```
Jarvis 1.0.0-rc.1
Automated validation: PASS
Clean Mac validation: PENDING
Code signing/notarization: OPTIONAL PENDING
Release tag: BLOCKED
Phase 10: BLOCKED
```

**Versión bajo prueba:** `1.0.0-rc.1`  
**Estado release:** ⬜ **NO PASS** — promoción a `v1.0.0` bloqueada  
**Validación automatizada (estación de desarrollo):** ✅ `READY_FOR_CLEAN_MAC` — ver `RELEASE_VALIDATION_LOG.md` (17 PASS / 1 WARN / 0 FAIL)

| Campo | Valor |
|-------|--------|
| Fecha Mac limpio | _______________ |
| Hardware | _______________ |
| macOS | _______________ |
| Operador | _______________ |

## Siguiente paso operativo (único)

1. Abrir `dist/Jarvis-1.0.0-rc.1.dmg` en un Mac limpio.
2. Ejecutar `Install.command`.
3. Completar instalación, permisos macOS, Ollama/modelos y onboarding.
4. Probar flujo crítico (voz, memoria, RAG, skills, captura, backup/restore).
5. Visión: confirmar `Vision: degraded` en `--health` (PASS base) — no instalar Homebrew/llava salvo prueba opt-in.
6. Marcar este documento → **PASS**.

Solo entonces: promoción oficial a Jarvis v1.0.0 (VERSION, CHANGELOG, RELEASE_NOTES, `git tag v1.0.0`).

## 0. Pre-requisitos en el Mac limpio

- [ ] Montar `dist/Jarvis-1.0.0-rc.1.dmg` **o** clonar el repo
- [ ] Python 3.12 (`brew install python@3.12`) si usas instalador standalone
- [ ] [Ollama](https://ollama.com) instalado y en marcha
- [ ] Modelos base: `ollama pull llama3.2:3b && ollama pull nomic-embed-text`
- [ ] **Red** durante `Install.command` (pip descarga deps; el DMG es bootstrap, no runtime completo)
- [ ] **Visión NO requerida para PASS 1.0.0** — sin llava/tesseract, espera `Vision: degraded` y continúa

## 1. Instalación sin Poetry (prioridad)

Opción A — standalone (recomendada para “sin Poetry”):

```bash
# Desde el repo (o carpeta del DMG si incluye el código)
./scripts/install_standalone_macos.sh
open ~/Applications/Jarvis.app
```

- [ ] Instala sin escribir `poetry` a mano
- [ ] Arranca como aplicación (`Jarvis.app`)
- [ ] `~/Library/Application\ Support/Jarvis/venv/bin/jarvis doctor` sin fallos críticos (exit ≠ 2)

Opción B — Poetry (desarrollo):

```bash
./scripts/install_macos.sh
poetry run jarvis doctor
```

## 2. Primera ejecución / onboarding

- [ ] Onboarding desde cero (`jarvis onboard` o diálogo GUI)
- [ ] Nombre de usuario
- [ ] Micrófono OK o advertencia clara
- [ ] Voz elegida
- [ ] Carpeta de conocimiento
- [ ] Backup inicial

## 3. Permisos macOS

- [ ] Micrófono
- [ ] Grabación de pantalla
- [ ] Accesibilidad
- [ ] Notificaciones
- [ ] _(Opcional)_ `jarvis autostart install`

## 4. Flujo crítico (happy path)

| Caso | OK |
|------|----|
| Arranque → Hey Jarvis → STT → LLM → TTS | [ ] |
| «¿Qué hora es?» | [ ] |
| «Recuerda que mi nombre es…» | [ ] |
| Consulta RAG / documentos | [ ] |
| Abrir aplicación | [ ] |
| Captura de pantalla | [ ] |
| `--health` → `Vision: degraded` (PASS base; visión opt-in) | [ ] |
| «¿Qué aparece en mi pantalla?» | [ ] _(opcional — solo si instalaste llava+tesseract)_ |
| Auditoría visible (GUI / DB) | [ ] |

> En desarrollo, el happy path **sin wake** ya pasó vía `./scripts/release_validate.sh`.
> En Mac limpio debe repetirse **con wake word y voz real**.

## 5. Recuperación

- [ ] Cerrar Jarvis forzosamente (Force Quit)
- [ ] Reiniciar Mac
- [ ] Abrir de nuevo
- [ ] Memoria intacta
- [ ] Configuración intacta
- [ ] Plugins intactos
- [ ] Índices RAG intactos

Automatizado en estación de build: backup → wipe → restore **PASS**.

## 6. Privacidad

- [ ] `jarvis privacy export` incluye perfil, memoria, preferencias, refs de docs, config
- [ ] `jarvis privacy wipe --yes` deja memoria personal vacía
- [ ] Restaurar desde backup si se necesita seguir probando

## 7. Firma / Gatekeeper (final 1.0.0)

- [ ] Abrir `.app` sin bloqueo severo (clic derecho → Abrir aceptable en RC)
- [ ] `./scripts/codesign_and_notarize.sh` con `JARVIS_CODESIGN_ID` + notary profile
- [ ] Usuario abre `Jarvis-1.0.0.dmg` sin advertencia Gatekeeper

## Resultado

- [ ] **PASS** — listo para promover a 1.0.0 + tag `v1.0.0`
- [ ] **FAIL** — anotar bloqueadores abajo y en `RELEASE_REPORT.md`

### Bloqueadores / notas

```
(espacio libre)
```

## Promoción (solo si PASS)

```bash
# NO ejecutar hasta este checklist = PASS
echo 1.0.0 > VERSION
# actualizar CHANGELOG + RELEASE_NOTES
# poetry version 1.0.0
# git tag v1.0.0 && git push origin v1.0.0
```
