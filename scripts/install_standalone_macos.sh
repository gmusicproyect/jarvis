#!/usr/bin/env bash
# Instalación standalone en macOS: venv + pip (sin Poetry en el día a día).
# Si el origen está en un DMG (/Volumes) o no es escribible, copia el código a
# ~/Library/Application Support/Jarvis/repo y crea el venv ahí.
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_SUPPORT="${HOME}/Library/Application Support/Jarvis"
REPO_DEST="${APP_SUPPORT}/repo"
VENV="${APP_SUPPORT}/venv"
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

echo "==> Jarvis — instalación standalone (sin Poetry obligatorio)"

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Se necesita Python 3.12. Instala con: brew install python@3.12"
  exit 1
fi

_is_ephemeral_or_readonly() {
  local root="$1"
  case "$root" in
    /Volumes/*) return 0 ;;
  esac
  if ! (touch "${root}/.jarvis_write_test" 2>/dev/null && rm -f "${root}/.jarvis_write_test"); then
    return 0
  fi
  return 1
}

ROOT="$SCRIPT_ROOT"
if _is_ephemeral_or_readonly "$SCRIPT_ROOT"; then
  echo "==> Origen en DMG / solo lectura — copiando a:"
  echo "    ${REPO_DEST}"
  mkdir -p "$REPO_DEST"
  rsync -a \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude 'venv' \
    --exclude '.runtime' \
    --exclude 'dist' \
    --exclude 'data/backups' \
    --exclude 'data/chroma' \
    --exclude 'data/chroma_rag' \
    --exclude 'data/exports' \
    --exclude 'data/screenshots' \
    --exclude 'data/logs' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude 'poetry.lock' \
    "${SCRIPT_ROOT}/" "${REPO_DEST}/"
  ROOT="$REPO_DEST"
else
  # Instalación desde clone/writable: mantener repo en sitio y enlazar desde App Support
  mkdir -p "$APP_SUPPORT"
  ln -sfn "$ROOT" "$REPO_DEST"
fi

cd "$ROOT"
mkdir -p "$APP_SUPPORT"

if [[ ! -x "${VENV}/bin/python" ]]; then
  echo "==> Creando venv en Application Support/Jarvis/venv"
  python3.12 -m venv "$VENV"
fi

echo "==> Instalando Jarvis + GUI en el venv"
"${VENV}/bin/pip" install -U pip wheel setuptools
"${VENV}/bin/pip" install -e ".[gui]"

# TTS opcional (Apple Silicon)
if [[ "$(uname -m)" == "arm64" ]]; then
  "${VENV}/bin/pip" install -q mlx-audio misaki phonemizer-fork espeakng-loader || true
fi

ln -sfn "$VENV" "${APP_SUPPORT}/venv"
echo "${VENV}/bin/python" > "${APP_SUPPORT}/python.path"

# python.path local solo si el repo es escribible (dev)
if mkdir -p "${ROOT}/.runtime" 2>/dev/null; then
  echo "${VENV}/bin/python" > "${ROOT}/.runtime/python.path"
fi

# CLI en PATH del usuario
mkdir -p "${HOME}/.local/bin"
ln -sfn "${VENV}/bin/jarvis" "${HOME}/.local/bin/jarvis"

cat > "${APP_SUPPORT}/install.json" <<EOF
{
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo": "$ROOT",
  "python": "${VENV}/bin/python",
  "method": "standalone_venv",
  "source": "$SCRIPT_ROOT"
}
EOF

echo "==> Creando Jarvis.app (launcher sin Poetry)"
"$ROOT/scripts/create_app_bundle.sh" "${HOME}/Applications/Jarvis.app"

echo ""
echo "Listo. Arranque sin Poetry:"
echo "  open \"${HOME}/Applications/Jarvis.app\""
echo "  o: jarvis gui   (vía ~/.local/bin)"
echo "  o: \"${VENV}/bin/jarvis\" gui"
echo ""
echo "Primera vez: jarvis onboard"
echo "Diagnóstico: jarvis doctor"
echo "PATH tip: asegúrate de que ~/.local/bin esté en tu PATH"
