# Guía de usuario — Jarvis

## Qué es

Asistente personal local-first: voz, memoria, documentos (RAG), automatización, visión y panel de escritorio.

## Uso básico

1. Abre `poetry run jarvis gui`.
2. Pulsa **Iniciar** (o usa la bandeja).
3. Di **Hey Jarvis** y da una orden.
4. También puedes escribir en la pestaña Conversación.

## Ejemplos

- «Abre Visual Studio Code»
- «¿Qué dice el manual sobre vacaciones?»
- «¿Qué hay en mi pantalla?»
- «Guarda esta captura en mi base de conocimiento»
- «Recuerda que mi proyecto se llama Atlas»

## Configuración

Pestaña **Configuración** en la GUI, o edita `config/config.yaml`.

## Plugins

```bash
poetry run jarvis plugins list
poetry run jarvis plugins install ./plugins/echo_plugin
```

## Modelos

```bash
poetry run jarvis models list
poetry run jarvis models pull llama3.2:3b
poetry run jarvis models pull llava
poetry run jarvis models pull nomic-embed-text
```

## Backup

```bash
poetry run jarvis backup create
poetry run jarvis backup list
poetry run jarvis backup restore data/backups/jarvis-backup-….zip
```
