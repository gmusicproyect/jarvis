# Checklist — Mac limpio (Jarvis 1.0 RC)

```
Jarvis 1.0.0-rc.1
Automated validation: PASS
Clean Mac validation: PENDING
Code signing/notarization: OPTIONAL PENDING
Release tag: BLOCKED
Phase 10: BLOCKED
```

```text
ARTEFACTO BAJO VALIDACIÓN
  Archivo:       Jarvis-1.0.0-rc.1.dmg  (612K)
  Commit ancla:  741dd825567f17deb1a76d7dc9837b86fc12d24e
  SHA-256:       aebebe2478f51b105f94cd005d3b5c486f68829520f2a3069498357819d7e57c

PASO -1 — ¿ES REALMENTE MAC LIMPIO?
  which ollama; ollama list 2>/dev/null; which tesseract; ls ~/.jarvis 2>/dev/null
  Todo vacío / not found. Si ya hubo Ollama+llava u otra instalación Jarvis,
  NO es Mac limpio: limpia, o el criterio FAIL de P0-2 (--health Vision: on
  sin deps) no cuenta en esa máquina.

PASO 0 — EN EL MAC LIMPIO, ANTES DE INSTALAR
  shasum -a 256 <ruta>/Jarvis-1.0.0-rc.1.dmg
  Debe coincidir carácter por carácter. Si no coincide → FAIL, no instalar.

PASO 1 — REQUISITO DE ENTORNO
  Conexión a internet disponible. El DMG es bootstrap: descarga deps (pip),
  y requiere Ollama + llama3.2:3b + nomic-embed-text durante/tras la instalación.

PASS BASE — requiere TODOS:
  [ ] Install.command completa sin pasos manuales no documentados
  [ ] Onboarding completo
  [ ] Permisos macOS concedidos (micrófono, accesibilidad, captura)
  [ ] Ollama + llama3.2:3b + nomic-embed-text quedan instalados por el flujo
  [ ] Voz E2E: wake "hey jarvis" → STT → respuesta → TTS audible
  [ ] Memoria persiste tras reinicio de la app
  [ ] RAG responde sobre knowledge/
  [ ] Al menos una skill ejecuta
  [ ] Captura / automatización funcionan con permisos concedidos
  [ ] Backup y restore completan
  [ ] jarvis --health → "Vision: degraded"   ← ESPERADO. No es fallo.
  [ ] jarvis doctor → 0 fail

CAPTURAR EN LA SESIÓN (para RELEASE_VALIDATION_LOG, PASS o FAIL):
  [ ] sha256 confirmado en esa máquina
  [ ] salida de jarvis doctor
  [ ] salida de jarvis --health

FAIL si:
  - El sha256 no coincide
  - Cualquier "fail" en doctor
  - El camino de voz no completa de extremo a extremo
  - --health reporta "Vision: on" sin llava ni tesseract  ← regresión de P0-2
    (solo válido si PASO -1 confirmó máquina limpia)

SI FAIL O SESIÓN INTERRUMPIDA:
  Estado = FAIL o PENDING. Nunca "casi PASS".
  Un arreglo genera commit nuevo → DMG nuevo → sha256 nuevo.
  No reutilices esta tarjeta con hash viejo y casillas nuevas.

FUERA DE ALCANCE (no bloquea el PASS de 1.0.0):
  - Visión funcional (opt-in, post-1.0.0)
  - Tiempo y tamaño de descarga de modelos
  - Cerrar P1-3 (cobertura 49%) — sigue abierto tras un PASS

Estado: PENDING
Marcado por: ____________  Fecha: __________  Máquina: __________
```

**Quién marca PASS:** solo el operador humano en hardware real. Ni Cursor ni Claude pueden ejecutar ni firmar este checklist.

**Versión bajo prueba:** `1.0.0-rc.1`  
**Estado release:** ⬜ **NO PASS** — promoción a `v1.0.0` bloqueada  
**Validación automatizada (estación de desarrollo):** ✅ `READY_FOR_CLEAN_MAC` — ver `RELEASE_VALIDATION_LOG.md`

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
