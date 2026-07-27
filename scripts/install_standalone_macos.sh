#!/usr/bin/env bash
# Instalación standalone en macOS: venv + pip (sin usar Poetry en el día a día).
# Poetry solo se usa si ya está; si no, crea .runtime/venv con pip.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RUNTIME="$ROOT/.runtime"
VENV="$RUNTIME/venv"
APP_SUPPORT="$HOME/Library/Application Support/Jarvis"
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

echo "==> Jarvis — instalación standalone (sin Poetry obligatorio)"

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Se necesita Python 3.12. Instala con: brew install python@3.12"
  exit 1
fi

mkdir -p "$RUNTIME" "$APP_SUPPORT"
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "==> Creando venv en .runtime/venv"
  python3.12 -m venv "$VENV"
fi

echo "==> Instalando Jarvis + GUI en el venv"
"$VENV/bin/pip" install -U pip wheel setuptools
"$VENV/bin/pip" install -e ".[gui]"

# TTS opcional (Apple Silicon)
if [[ "$(uname -m)" == "arm64" ]]; then
  "$VENV/bin/pip" install -q mlx-audio misaki phonemizer-fork espeakng-loader || true
fi

# Enlace estable para el .app
ln -sfn "$ROOT" "$APP_SUPPORT/repo"
ln -sfn "$VENV" "$APP_SUPPORT/venv"
echo "$VENV/bin/python" > "$APP_SUPPORT/python.path"
echo "$VENV/bin/python" > "$RUNTIME/python.path"

# Marcador de instalación
cat > "$APP_SUPPORT/install.json" <<EOF
{
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo": "$ROOT",
  "python": "$VENV/bin/python",
  "method": "standalone_venv"
}
EOF

echo "==> Creando Jarvis.app (launcher sin Poetry)"
"$ROOT/scripts/create_app_bundle.sh" "$HOME/Applications/Jarvis.app"

echo ""
echo "Listo. Arranque sin Poetry:"
echo "  open \"$HOME/Applications/Jarvis.app\""
echo "  o: \"$VENV/bin/jarvis\" gui"
echo "  o: \"$VENV/bin/python\" -m jarvis doctor"
echo ""
echo "Primera vez: \"$VENV/bin/jarvis\" onboard"
echo "Diagnóstico: \"$VENV/bin/jarvis\" doctor"
