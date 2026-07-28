#!/usr/bin/env bash
# Captura evidencia de la sesión Mac limpio (PASS o FAIL).
# Uso:
#   ./scripts/clean_mac_capture.sh [/ruta/a/Jarvis-1.0.0-rc.1.dmg]
# Salida por defecto:
#   ~/Desktop/jarvis_clean_mac_capture_YYYYMMDD_HHMM.txt
#
# No marca el checklist. Solo reúne evidencias para pegar en el chat / log.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

EXPECTED_SHA256="44ba93a379f076d9f347d8b6ae496528f868d4e19b25d1e2acd787b2b5c16851"
EXPECTED_ANCHOR="910d3dcbdf080a57a632de28bcdb878a36889418"
DMG="${1:-}"
STAMP="$(date +%Y%m%d_%H%M)"
DEFAULT_OUT="$HOME/Desktop/jarvis_clean_mac_capture_${STAMP}.txt"
FALLBACK_OUT="/tmp/jarvis_clean_mac_capture_${STAMP}.txt"
OUT="${JARVIS_CAPTURE_OUT:-$DEFAULT_OUT}"

# Si Desktop no es escribible (sandbox / permisos), usa /tmp
if ! touch "$OUT" 2>/dev/null; then
  OUT="$FALLBACK_OUT"
fi

resolve_jarvis() {
  if command -v jarvis >/dev/null 2>&1; then
    echo "jarvis"
    return
  fi
  local py
  if [[ -x "$HOME/Library/Application Support/Jarvis/venv/bin/jarvis" ]]; then
    echo "$HOME/Library/Application Support/Jarvis/venv/bin/jarvis"
    return
  fi
  if [[ -x "$ROOT/.runtime/venv/bin/jarvis" ]]; then
    echo "$ROOT/.runtime/venv/bin/jarvis"
    return
  fi
  if command -v poetry >/dev/null 2>&1 && [[ -f "$ROOT/pyproject.toml" ]]; then
    echo "poetry run jarvis"
    return
  fi
  echo ""
}

find_dmg() {
  if [[ -n "$DMG" && -f "$DMG" ]]; then
    echo "$DMG"
    return
  fi
  for cand in \
    "$ROOT/dist/Jarvis-1.0.0-rc.1.dmg" \
    "/Volumes/Jarvis"*/Jarvis-1.0.0-rc.1.dmg \
    "$HOME/Downloads/Jarvis-1.0.0-rc.1.dmg" \
    "$HOME/Desktop/Jarvis-1.0.0-rc.1.dmg"
  do
    # glob may no expand
    for f in $cand; do
      if [[ -f "$f" ]]; then
        echo "$f"
        return
      fi
    done
  done
  echo ""
}

{
  echo "JARVIS CLEAN MAC CAPTURE"
  echo "generated_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "host=$(hostname 2>/dev/null || echo unknown)"
  echo "user=$(whoami 2>/dev/null || echo unknown)"
  echo "macos=$(sw_vers 2>/dev/null | tr '\n' ' ' || uname -a)"
  echo "expected_anchor=$EXPECTED_ANCHOR"
  echo "expected_sha256=$EXPECTED_SHA256"
  echo

  echo "===== PASO -1a: inventario sistema (alcance PASS / P1-5) ====="
  which -a ollama tesseract brew python3 2>&1 || true
  ls -d /Applications/Ollama.app /opt/homebrew 2>&1 || true
  ls "$HOME/.ollama/models" 2>&1 || true
  echo

  echo "===== PASO -1b: residuos Jarvis ====="
  ls -d "$HOME/.jarvis" "$HOME/Applications/Jarvis.app" \
    "$HOME/Library/Application Support/"*[Jj]arvis* \
    "$HOME/Library/Preferences/"*[Jj]arvis* \
    "$HOME/Library/Logs/"*[Jj]arvis* \
    "$HOME/Library/Caches/"*[Jj]arvis* 2>&1 || true
  which jarvis 2>&1 || true
  echo

  echo "===== PASO -1 (legacy paths) ====="
  echo "--- which ollama ---"
  which ollama 2>&1 || true
  echo "--- ollama list ---"
  ollama list 2>&1 || true
  echo "--- which tesseract ---"
  which tesseract 2>&1 || true
  echo "--- ls ~/.jarvis ---"
  ls -la "$HOME/.jarvis" 2>&1 || true
  echo "--- ls Application Support/Jarvis ---"
  ls -la "$HOME/Library/Application Support/Jarvis" 2>&1 || true
  echo

  echo "===== PASO 0: SHA-256 del DMG ====="
  DMG_PATH="$(find_dmg)"
  if [[ -z "$DMG_PATH" ]]; then
    echo "DMG_NOT_FOUND"
    echo "Pasa la ruta: $0 /ruta/Jarvis-1.0.0-rc.1.dmg"
    echo "sha256_match=UNKNOWN"
  else
    echo "dmg_path=$DMG_PATH"
    ACTUAL="$(shasum -a 256 "$DMG_PATH" | awk '{print $1}')"
    echo "sha256_actual=$ACTUAL"
    if [[ "$ACTUAL" == "$EXPECTED_SHA256" ]]; then
      echo "sha256_match=YES"
    else
      echo "sha256_match=NO"
      echo "FAIL: el DMG no coincide con el ancla 741dd82. No instalar / no marcar PASS."
    fi
  fi
  echo

  JARVIS_CMD="$(resolve_jarvis)"
  echo "===== jarvis binary (¿DMG o repo de desarrollo?) ====="
  echo "jarvis_cmd=${JARVIS_CMD:-NOT_FOUND}"
  if command -v jarvis >/dev/null 2>&1; then
    echo -n "which_jarvis="
    which jarvis
    if command -v readlink >/dev/null 2>&1; then
      echo -n "readlink="
      readlink -f "$(which jarvis)" 2>/dev/null || readlink "$(which jarvis)" 2>/dev/null || true
    fi
    case "$(which jarvis 2>/dev/null)$(readlink -f "$(which jarvis)" 2>/dev/null || true)" in
      */Users/*/jarvis/*|*/jarvis/src/*)
        echo "WARNING: jarvis parece apuntar al árbol de desarrollo — el PASS del DMG no cuenta"
        ;;
    esac
  fi
  echo

  if [[ -z "$JARVIS_CMD" ]]; then
    echo "===== jarvis doctor ====="
    echo "SKIPPED (jarvis no instalado aún — corre esto DESPUÉS de Install.command)"
    echo
    echo "===== jarvis --health ====="
    echo "SKIPPED"
  else
    echo "===== jarvis --version ====="
    # shellcheck disable=SC2086
    eval $JARVIS_CMD --version 2>&1 || true
    echo
    echo "===== jarvis doctor ====="
    # shellcheck disable=SC2086
    eval $JARVIS_CMD doctor 2>&1 || true
    echo
    echo "===== jarvis --health ====="
    # shellcheck disable=SC2086
    eval $JARVIS_CMD --health 2>&1 || true
  fi
  echo

  echo "===== doctor standalone (PASS/FAIL estilo) ====="
  if command -v python3 >/dev/null 2>&1; then
    python3 "$ROOT/scripts/jarvis_doctor_standalone.py" 2>&1 || true
  else
    echo "SKIPPED (no python3)"
  fi
  echo

  echo "===== NOTAS DEL OPERADOR (rellenar) ====="
  echo "checklist_result=PENDING   # PASS | FAIL | PENDING"
  echo "voice_e2e=                 # OK | FAIL"
  echo "memory_persist=            # OK | FAIL"
  echo "rag=                       # OK | FAIL"
  echo "skill=                     # OK | FAIL"
  echo "screenshot_automation=     # OK | FAIL"
  echo "backup_restore=            # OK | FAIL"
  echo "vision_health_line=        # pegar la línea Vision: ..."
  echo "ollama_preexistente="
echo "homebrew_preexistente="
echo "tesseract_preexistente="
echo "P1-5_cold_start_instalador=ABIERTO_si_Camino_B"
echo "machine_notes="
  echo
  echo "===== FIN ====="
  echo "Pega este archivo completo en el chat (Cursor/Claude) con PASS o FAIL."
} | tee "$OUT"

echo
echo "Captura escrita en: $OUT"
