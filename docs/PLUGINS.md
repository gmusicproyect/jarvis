# Plugins Jarvis

## Estructura

```
plugin/
 ├── manifest.yaml
 ├── skill.py
 ├── config.yaml
 ├── README.md
 └── tests/
```

## manifest.yaml

```yaml
name: spotify_plugin
version: 1.0.0
author: Tú
description: Control de Spotify
permissions:
  - audio_control
dependencies: []
skills:
  - play_music
compatibility: ">=0.1.0"
entry: skill.py
enabled: true
```

## CLI

```bash
jarvis plugins list
jarvis plugins install ./ruta/al/plugin
jarvis plugins enable nombre
jarvis plugins disable nombre
jarvis plugins remove nombre
```

## Marketplace (preparado)

`StubMarketplace` define el contrato (`search`, `fetch`, `verify`) para un repositorio remoto con firma y versionado. Aún no hay store público.

## Permisos conocidos

`safe`, `confirm`, `restricted`, `audio_control`, `filesystem`, `network`, `browser`, `shell`, `vision`, `notifications`.
