#!/usr/bin/env bash
# Fase 0: healthcheck. Fase 1+: lanzará el orchestrator.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="$HOME/.local/bin:$PATH"
exec poetry run jarvis "$@"
