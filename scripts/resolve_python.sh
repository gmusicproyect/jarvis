#!/usr/bin/env bash
# Resuelve el intérprete Python de Jarvis sin exigir `poetry` en el PATH.
# Prioridad:
#   JARVIS_PYTHON → archivo python.path → .runtime/venv → .venv
#   → Application Support → Poetry env → error (nunca system bare)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Si vive en Contents/Resources, la raíz del repo está en python.path / JARVIS_ROOT
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -f "$SCRIPT_DIR/../MacOS/Jarvis" ]]; then
  # Estamos dentro del .app Resources — ROOT real lo da el launcher; aquí solo pins locales
  ROOT="${JARVIS_ROOT:-$ROOT}"
fi

if [[ -n "${JARVIS_PYTHON:-}" && -x "${JARVIS_PYTHON}" ]]; then
  echo "$JARVIS_PYTHON"
  exit 0
fi

for pin in \
  "$SCRIPT_DIR/python.path" \
  "${JARVIS_ROOT:-}/.runtime/python.path" \
  "$HOME/Library/Application Support/Jarvis/python.path"
do
  if [[ -n "$pin" && -f "$pin" ]]; then
    pinned="$(tr -d '[:space:]' < "$pin")"
    if [[ -x "$pinned" ]]; then
      echo "$pinned"
      exit 0
    fi
  fi
done

# ROOT del repo cuando el script está en scripts/
if [[ -f "$SCRIPT_DIR/../pyproject.toml" ]]; then
  ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

candidates=(
  "$ROOT/.runtime/venv/bin/python"
  "$ROOT/.venv/bin/python"
  "$HOME/Library/Application Support/Jarvis/venv/bin/python"
)

for py in "${candidates[@]}"; do
  if [[ -x "$py" ]] && "$py" -c "import jarvis" >/dev/null 2>&1; then
    echo "$py"
    exit 0
  fi
done

export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"
if command -v poetry >/dev/null 2>&1 && [[ -f "$ROOT/pyproject.toml" ]]; then
  env_py="$(cd "$ROOT" && poetry env info -p 2>/dev/null || true)"
  if [[ -n "$env_py" && -x "$env_py/bin/python" ]]; then
    echo "$env_py/bin/python"
    exit 0
  fi
fi

echo "No se encontró un Python con Jarvis instalado." >&2
echo "Ejecuta: ./scripts/install_standalone_macos.sh" >&2
exit 1
