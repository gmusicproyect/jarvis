# Checklist — Instalación fresca de Jarvis (1.0.0-rc.1)

> **Cambio oficial de criterio (2026-07-27)**  
> Ya **no** se exige un Mac de fábrica / virgen.  
> Se exige una **instalación fresca de Jarvis**: el producto no debe estar preinstalado
> en esa cuenta (PASO -1). Preferir **cuenta nueva**; wipe dirigido solo si hace falta.
> Camino B valida la app; el cold-start del instalador sin Ollama/Homebrew queda como **P1-5**.
>
> Objetivo: probar el DMG como lo haría un usuario nuevo, sin medir el entorno Poetry del repo.

```
Jarvis 1.0.0-rc.1
Automated validation: PASS
Install-fresh validation: PENDING
Code signing/notarization: OPTIONAL PENDING
Release tag: BLOCKED
Phase 10: BLOCKED
```

```text
ARTEFACTO BAJO VALIDACIÓN
  Archivo:       Jarvis-1.0.0-rc.1.dmg  (728K)
  Commit ancla:  2b1ea98 (fix .app python.path / kLSNoExecutableErr)
  SHA-256:       d1cc8cbcf2484463e40817023b1426edee892765b7c2d98205a875528b399210
  Nota: instalación actual en esta Mac ya es válida (venv App Support);
        el DMG nuevo es para reinstalaciones / capturar Install limpio.

QUÉ CUENTA COMO "FRESCO" (no hace falta Mac nueva)
  Preferir: cuenta de macOS NUEVA (limpia por construcción).
  Alternativa: misma cuenta + wipe dirigido + inventario (abajo).
  - Residuos Jarvis en la cuenta deben estar vacíos (PASO -1).
  - Ollama/Homebrew a nivel sistema PUEDEN existir: el PASS valida la app,
    NO el cold-start completo del instalador (ver P1-5 / alcance).

PASO -1a — Inventario de sistema (define qué NO verifica este PASS)
  which -a ollama tesseract brew python3
  ls -d /Applications/Ollama.app /opt/homebrew 2>/dev/null
  ls ~/.ollama/models 2>/dev/null
  → Pegar salida en "Alcance del PASS — no verificado" abajo.

PASO -1b — Residuos Jarvis (debe salir vacío antes de instalar)
  ls -d ~/.jarvis /Applications/Jarvis.app \
        ~/Library/Application\ Support/*[Jj]arvis* \
        ~/Library/Preferences/*[Jj]arvis* \
        ~/Library/Logs/*[Jj]arvis* \
        ~/Library/Caches/*[Jj]arvis* 2>/dev/null
  which jarvis 2>/dev/null
  → Todo vacío. Si no: wipe o usa otra cuenta.
  Si reutilizas la misma cuenta (TCC ya concedidos pueden falsear onboarding):
    defaults read /Applications/Jarvis.app/Contents/Info.plist CFBundleIdentifier
    # tccutil reset All <bundle-id>   # app cerrada

PASO 0 — SHA-256 del DMG
  shasum -a 256 <ruta>/Jarvis-1.0.0-rc.1.dmg
  Debe ser: d1cc8cbcf2484463e40817023b1426edee892765b7c2d98205a875528b399210
  Si no coincide → FAIL, no instalar.

PASO 1 — Instalar desde el DMG (no desde poetry run en el repo)
  [ ] Install.command (o install_standalone_macos.sh desde JarvisSource)
  [ ] Red disponible (bootstrap descarga deps)
  [ ] Onboarding (debe ejecutarse de verdad — no saltarlo por estado viejo)
  [ ] Permisos: micrófono (+ pantalla/accesibilidad si pruebas captura)

PASO 1b — ¿Estás midiendo el DMG o el árbol de desarrollo?
  which jarvis && readlink -f "$(which jarvis)" 2>/dev/null || which jarvis
  → Debe apuntar a Application Support/Jarvis o al venv de la instalación.
  → NUNCA a /Users/.../jarvis (repo de desarrollo). Si apunta al repo → FAIL.

PASS BASE — todos:
  [ ] Voz E2E: Hey Jarvis → respuesta → TTS audible
  [ ] Memoria (“recuerda que…”) y sigue tras reiniciar la app
  [ ] RAG responde sobre knowledge/
  [ ] Al menos una skill (hora / abrir app)
  [ ] Backup create + restore OK
  [ ] jarvis --health → Vision: degraded   ← ESPERADO (visión opt-in)
  [ ] jarvis doctor → 0 fail
  [ ] Captura: sha256 + doctor + --health  (scripts/clean_mac_capture.sh)
  [ ] Alcance del PASS rellenado (inventario PASO -1a)

ALCANCE DEL PASS — no verificado (pegar inventario PASO -1a):
  ollama_preexistente=     # si/no
  homebrew_preexistente=   # si/no
  tesseract_preexistente=  # si/no
  notas=
  → Un PASS por Camino B deja P1-5 ABIERTO (cold-start instalador).

FAIL si:
  - sha256 no coincide
  - doctor con fail
  - voz E2E no completa
  - which jarvis apunta al repo de desarrollo
  - --health dice Vision: on sin llava/tesseract (regresión P0-2)
    solo cuenta si no tenías llava preinstalado

WIPE DIRIGIDO (solo si no puedes usar cuenta nueva)
  rm -rf ~/Library/Application\ Support/Jarvis
  rm -rf ~/.jarvis
  rm -rf ~/Applications/Jarvis.app
  # Opcional P0-2 a fondo: ollama rm llava

NO EXIGIDO PARA PASS:
  - Mac de fábrica / borrar Homebrew / todo Ollama
  - Visión funcional (llava + tesseract)
  - Cerrar P1-3 (cobertura 49%) ni P1-5 (cold-start instalador)

Estado: PENDING
Marcado por: ____________  Fecha: __________  Cuenta/Máquina: __________
```

**Quién marca PASS:** tú, en hardware real, tras una instalación fresca (no `poetry run` del repo de desarrollo).

**Captura de evidencias:**

```bash
chmod +x scripts/clean_mac_capture.sh
./scripts/clean_mac_capture.sh /ruta/Jarvis-1.0.0-rc.1.dmg
# → ~/Desktop/jarvis_clean_mac_capture_*.txt
```

| Campo | Valor |
|-------|--------|
| Fecha | _______________ |
| Hardware / cuenta | _______________ |
| macOS | _______________ |
| Operador | _______________ |

## Resultado

- [ ] **PASS** — listo para pedir promoción a 1.0.0
- [ ] **FAIL** — no reutilizar esta tarjeta; nuevo fix → nuevo DMG → nuevo sha256
- [ ] **PENDING** — sesión no terminada (nunca “casi PASS”)

### Notas

```
(espacio libre)
```

## Promoción (solo si PASS literal)

```bash
# NO ejecutar hasta este checklist = PASS
# Ver RELEASE_REPORT.md
```
