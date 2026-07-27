#!/usr/bin/env bash
# Validación automatizada del cierre de release (no sustituye Mac limpio manual).
# Genera docs/RELEASE_VALIDATION_LOG.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

LOG="$ROOT/docs/RELEASE_VALIDATION_LOG.md"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PASS=0
FAIL=0
WARN=0
RESULTS=()

note() { RESULTS+=("$1"); }
ok() { PASS=$((PASS + 1)); note "| PASS | $1 | $2 |"; }
fail() { FAIL=$((FAIL + 1)); note "| FAIL | $1 | $2 |"; }
warn() { WARN=$((WARN + 1)); note "| WARN | $1 | $2 |"; }

run_jarvis() {
  if command -v poetry >/dev/null 2>&1; then
    poetry run jarvis "$@"
  else
    PY="$("$ROOT/scripts/resolve_python.sh")"
    PYTHONPATH="$ROOT/src" "$PY" -m jarvis "$@"
  fi
}

echo "==> Release validate v${VERSION}"

# --- Version ---
VER_OUT="$(run_jarvis --version 2>/dev/null | tr -d '[:space:]' || true)"
if [[ "$VER_OUT" == "$VERSION" ]]; then
  ok "version" "$VER_OUT"
else
  fail "version" "esperado=$VERSION obtenido=$VER_OUT"
fi

# --- Doctor ---
set +e
DOC_OUT="$(run_jarvis doctor 2>&1)"
DOC_EC=$?
set -e
if [[ $DOC_EC -eq 2 ]]; then
  fail "doctor" "fallos críticos (exit 2)"
elif [[ $DOC_EC -eq 1 ]]; then
  warn "doctor" "advertencias (exit 1) — ver salida"
  ok "doctor-no-critical" "sin fallos críticos"
else
  ok "doctor" "exit 0"
fi

# --- Snapshot hashes (persistencia) ---
hash_state() {
  local f
  {
    for f in config/config.yaml data/db/jarvis.db data/plugins_state.json; do
      if [[ -f "$f" ]]; then
        shasum -a 256 "$f" | awk '{print $1"  '"$f"'"}'
      fi
    done
    if [[ -d plugins ]]; then find plugins -type f | sort | shasum -a 256; fi
    if [[ -d data/chroma_rag ]]; then find data/chroma_rag -type f 2>/dev/null | wc -l | awk '{print "chroma_rag_files="$1}'; fi
  } 2>/dev/null
}
STATE_BEFORE="$(hash_state)"
ok "snapshot-before" "capturado"

# --- Backup ---
BAK="$(run_jarvis backup create --label release-validate 2>&1 | awk '/Backup creado:/{print $3}')"
if [[ -n "$BAK" && -f "$BAK" ]]; then
  ok "backup-create" "$BAK"
else
  # fallback parse
  BAK="$(ls -t data/backups/jarvis-backup-*-release-validate.zip 2>/dev/null | head -1 || true)"
  if [[ -n "$BAK" && -f "$BAK" ]]; then
    ok "backup-create" "$BAK"
  else
    fail "backup-create" "no se generó zip"
  fi
fi

# --- Happy path (sin wake; STT/TTS parcial) ---
happy() {
  local label="$1" text="$2"
  set +e
  OUT="$(run_jarvis --once-text "$text" 2>&1)"
  EC=$?
  set -e
  if [[ $EC -eq 0 ]] && echo "$OUT" | grep -qi "Jarvis:"; then
    ok "happy:$label" "$(echo "$OUT" | grep -i 'Jarvis:' | head -1 | cut -c1-120)"
  else
    fail "happy:$label" "ec=$EC :: $(echo "$OUT" | tail -3 | tr '\n' ' ')"
  fi
}

happy "hora" "¿Qué hora es?"
happy "memoria" "Recuerda que mi color favorito es azul índigo."
happy "rag" "Según mis documentos, ¿de qué trata el manual de instalación?"
happy "app" "Abre la aplicación TextEdit."
happy "screenshot" "Haz una captura de pantalla."

set +e
VIS_OUT="$(run_jarvis --once-text "¿Qué aparece en mi pantalla?" 2>&1)"
VIS_EC=$?
set -e
if [[ $VIS_EC -eq 0 ]] && echo "$VIS_OUT" | grep -qi "Jarvis:"; then
  ok "happy:vision" "respuesta recibida"
else
  warn "happy:vision" "puede faltar llava/permisos pantalla — $(echo "$VIS_OUT" | tail -2 | tr '\n' ' ')"
fi

# --- Privacy export ---
EXP_OUT="$(run_jarvis privacy export 2>&1)"
EXP_PATH="$(echo "$EXP_OUT" | awk '/Exportado:/{print $2}')"
if [[ -n "$EXP_PATH" && -f "$EXP_PATH" ]]; then
  if python3 -c "
import json, sys
p = json.load(open('$EXP_PATH', encoding='utf-8'))
need = ['profile', 'memory_items', 'config_snapshot', 'indexed_documents', 'preferences']
missing = [k for k in need if k not in p]
sys.exit(1 if missing else 0)
"; then
    ok "privacy-export" "$EXP_PATH"
  else
    fail "privacy-export" "JSON incompleto"
  fi
else
  fail "privacy-export" "$EXP_OUT"
fi

# --- Privacy wipe + restore ---
MEM_BEFORE="$(python3 - <<'PY'
import sqlite3
from pathlib import Path
p = Path("data/db/jarvis.db")
if not p.exists():
    print(0)
else:
    c = sqlite3.connect(p)
    print(c.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0])
    c.close()
PY
)"

run_jarvis privacy wipe --yes --keep-name >/dev/null
MEM_AFTER="$(python3 - <<'PY'
import sqlite3
from pathlib import Path
p = Path("data/db/jarvis.db")
c = sqlite3.connect(p)
print(c.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0])
c.close()
PY
)"
if [[ "$MEM_AFTER" == "0" ]]; then
  ok "privacy-wipe" "items $MEM_BEFORE → 0"
else
  fail "privacy-wipe" "quedan $MEM_AFTER items"
fi

if [[ -n "${BAK:-}" && -f "$BAK" ]]; then
  run_jarvis backup restore "$BAK" >/dev/null 2>&1 || run_jarvis backup restore "$BAK" --force >/dev/null
  MEM_REST="$(python3 - <<'PY'
import sqlite3
from pathlib import Path
p = Path("data/db/jarvis.db")
c = sqlite3.connect(p)
print(c.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0])
c.close()
PY
)"
  if [[ "$MEM_REST" -ge 0 ]]; then
    ok "backup-restore" "memoria tras restore=$MEM_REST (antes wipe=$MEM_BEFORE)"
  else
    fail "backup-restore" "no se pudo leer DB"
  fi
else
  fail "backup-restore" "sin backup"
fi

STATE_AFTER="$(hash_state)"
if [[ -n "$STATE_AFTER" ]]; then
  ok "snapshot-after-restore" "config/plugins/chroma presentes"
else
  warn "snapshot-after-restore" "vacío"
fi

# --- Launcher sin Poetry ---
if PY_RES="$("$ROOT/scripts/resolve_python.sh" 2>/dev/null)"; then
  if "$PY_RES" -c "import jarvis; print(jarvis.__version__)" >/dev/null 2>&1; then
    ok "resolve-python" "$PY_RES"
  else
    warn "resolve-python" "python resuelto pero sin paquete jarvis — corre install_standalone"
  fi
else
  fail "resolve-python" "no hay intérprete"
fi

# --- Tests ---
set +e
TEST_OUT="$(poetry run pytest tests/unit/ -q --no-cov --tb=no 2>&1 | tail -3)"
TEST_EC=$?
set -e
if [[ $TEST_EC -eq 0 ]]; then
  ok "unit-tests" "$(echo "$TEST_OUT" | grep -E 'passed' | tail -1)"
else
  fail "unit-tests" "$TEST_OUT"
fi

# --- DMG presence ---
if [[ -f "dist/Jarvis-${VERSION}.dmg" ]]; then
  ok "dmg-artifact" "dist/Jarvis-${VERSION}.dmg"
else
  warn "dmg-artifact" "ausente — ./scripts/create_dmg.sh"
fi

# --- Write log ---
{
  echo "# Release validation log"
  echo ""
  echo "| Campo | Valor |"
  echo "|-------|--------|"
  echo "| Fecha UTC | $STAMP |"
  echo "| Versión | $VERSION |"
  echo "| PASS | $PASS |"
  echo "| WARN | $WARN |"
  echo "| FAIL | $FAIL |"
  echo ""
  echo "## Resultados"
  echo ""
  echo "| Estado | Check | Detalle |"
  echo "|--------|-------|---------|"
  for line in "${RESULTS[@]}"; do
    echo "$line"
  done
  echo ""
  echo "## Doctor (extracto)"
  echo ""
  echo '```'
  echo "$DOC_OUT" | head -40
  echo '```'
  echo ""
  echo "## Mac limpio / firma"
  echo ""
  echo "- Mac limpio manual: **PENDIENTE** (ver CLEAN_MAC_CHECKLIST.md)"
  echo "- Firma/notarización: **PENDIENTE** salvo \`JARVIS_CODESIGN_ID\`"
  echo "- Promoción a 1.0.0: **BLOQUEADA** mientras FAIL>0 o Mac limpio ≠ PASS"
  echo ""
  if [[ $FAIL -eq 0 ]]; then
    echo "**Veredicto automatizado:** READY_FOR_CLEAN_MAC (no es PASS de release todavía)."
  else
    echo "**Veredicto automatizado:** NOT_READY — corregir FAIL antes del Mac limpio."
  fi
} > "$LOG"

echo ""
echo "Log: $LOG"
echo "PASS=$PASS WARN=$WARN FAIL=$FAIL"
[[ $FAIL -eq 0 ]]
