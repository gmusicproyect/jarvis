#!/usr/bin/env bash
# Instala Poetry (si falta), deps del proyecto y pre-commit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v poetry >/dev/null 2>&1; then
  echo "Instalando Poetry..."
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
fi

# Preferir Python 3.12 LTS (evita incompatibilidades de IA/audio en 3.14+)
if command -v python3.12 >/dev/null 2>&1; then
  poetry env use python3.12
else
  echo "AVISO: python3.12 no encontrado. Instala con: brew install python@3.12"
  poetry env use python3
fi

poetry install --with dev
# Kokoro (Apple Silicon)
poetry run pip install -q mlx-audio misaki phonemizer-fork espeakng-loader
poetry run pre-commit install
echo "OK. Python: $(poetry run python -V)"
echo "Prueba: poetry run jarvis --health"
echo "Voz: poetry run jarvis"
