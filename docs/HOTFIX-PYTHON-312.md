# Hotfix — Python 3.12 LTS (2026-07-27)

## Cambio

| Antes | Después |
|-------|---------|
| Poetry env en Python **3.14** | Poetry env en Python **3.12.13** |
| `python = "^3.12"` (aceptaba 3.14) | `python = ">=3.12,<3.13"` |

## Pasos realizados

1. `brew install python@3.12`
2. `poetry env remove --all` + `poetry env use /opt/homebrew/bin/python3.12`
3. Regenerar `poetry.lock` + `poetry install --with dev`
4. `poetry run pip install mlx-audio misaki phonemizer-fork espeakng-loader`
5. `poetry run pytest` + `jarvis --health`

## Instalación en máquinas nuevas

```bash
brew install python@3.12   # macOS
cd ~/jarvis
poetry env use python3.12
./scripts/install.sh
```
