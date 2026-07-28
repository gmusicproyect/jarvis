# Checklist — Instalación fresca de Jarvis (1.0.0-rc.1)

> **Cambio oficial de criterio (2026-07-27)**  
> Ya **no** se exige un Mac de fábrica / virgen.  
> Se exige una **instalación fresca de Jarvis**: el producto no debe estar preinstalado
> en esa cuenta de usuario (PASO -1). Misma Mac de desarrollo: OK si usas
> **otra cuenta de macOS** o un wipe dirigido solo de Jarvis.
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
  Archivo:       Jarvis-1.0.0-rc.1.dmg  (612K)
  Commit ancla:  741dd825567f17deb1a76d7dc9837b86fc12d24e
  SHA-256:       aebebe2478f51b105f94cd005d3b5c486f68829520f2a3069498357819d7e57c

QUÉ CUENTA COMO "FRESCO" (no hace falta Mac nueva)
  - Cuenta de usuario de macOS sin Jarvis instalado, O
  - Misma cuenta tras quitar solo residuos de Jarvis (ver wipe abajo).
  - Ollama puede existir; lo que no debe existir es una instalación
    previa de Jarvis (App Support / venv / ~/.jarvis).
  - Si ya tienes llava y quieres validar P0-2, quita llava o usa otra cuenta.

PASO -1 — ¿Jarvis ya está instalado aquí?
  ls ~/Library/Application\ Support/Jarvis 2>/dev/null
  ls ~/.jarvis 2>/dev/null
  ls ~/Applications/Jarvis.app 2>/dev/null
  which jarvis 2>/dev/null
  → Todo vacío / not found. Si no: wipe dirigido (abajo) o usa otra cuenta.

PASO 0 — SHA-256 del DMG
  shasum -a 256 <ruta>/Jarvis-1.0.0-rc.1.dmg
  Debe ser: aebebe2478f51b105f94cd005d3b5c486f68829520f2a3069498357819d7e57c
  Si no coincide → FAIL, no instalar.

PASO 1 — Instalar desde el DMG (no desde poetry run en el repo)
  [ ] Install.command (o install_standalone_macos.sh desde JarvisSource)
  [ ] Red disponible (bootstrap descarga deps)
  [ ] Onboarding
  [ ] Permisos: micrófono (+ pantalla/accesibilidad si pruebas captura)

PASS BASE — todos:
  [ ] Voz E2E: Hey Jarvis → respuesta → TTS audible
  [ ] Memoria (“recuerda que…”) y sigue tras reiniciar la app
  [ ] RAG responde sobre knowledge/
  [ ] Al menos una skill (hora / abrir app)
  [ ] Backup create + restore OK
  [ ] jarvis --health → Vision: degraded   ← ESPERADO (visión opt-in)
  [ ] jarvis doctor → 0 fail
  [ ] Captura: sha256 + doctor + --health  (scripts/clean_mac_capture.sh)

FAIL si:
  - sha256 no coincide
  - doctor con fail
  - voz E2E no completa
  - --health dice Vision: on sin llava/tesseract (regresión P0-2)
    solo cuenta si no tenías llava preinstalado

WIPE DIRIGIDO (opcional, misma Mac — NO borra tu vida)
  # Solo residuos Jarvis; Ollama/modelos los dejas si quieres
  rm -rf ~/Library/Application\ Support/Jarvis
  rm -rf ~/.jarvis
  rm -rf ~/Applications/Jarvis.app
  # Opcional para probar P0-2 a fondo:
  # ollama rm llava

NO EXIGIDO PARA PASS:
  - Mac de fábrica
  - Borrar Homebrew / todo Ollama / fotos / mail
  - Visión funcional (llava + tesseract)
  - Cerrar P1-3 (cobertura 49%)

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
