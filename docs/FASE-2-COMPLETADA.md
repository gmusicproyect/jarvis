# Fase 2 — Memoria (sesión / SQLite / semántica)

## Tres capas

| Capa | Implementación | Persistencia |
|------|----------------|--------------|
| Sesión | `WindowSessionMemory` | RAM (ventana `short_term_turns`) |
| Persistente | `SQLitePersistentMemory` | `data/db/jarvis.db` |
| Semántica | `ChromaSemanticMemory` | `data/chroma` + embeddings Ollama |

## Interfaces (mismo patrón Fase 1)

- `SessionMemory`
- `PersistentMemory`
- `SemanticMemory`

Cambio de motor = nuevo provider + `config.yaml` (`persistent_provider`, `semantic_provider`).

## Comandos de voz / texto

- "Recuerda que mi nombre es…"
- "No olvides que…"
- "Guarda esta nota…"
- "¿Qué recuerdas sobre…?"
- "Olvida…"
- "Muéstrame mis notas."

## Decisión de diseño: LlamaIndex

En Fase 2 el índice semántico usa **Chroma + embeddings Ollama** directamente (menos peso, mismo almacén).

**LlamaIndex** se integra en **Fase 4 (RAG de documentos)** sobre el mismo `data/chroma`, sin romper esta API.

Si prefieres LlamaIndex ya en Fase 2, se puede envolver `ChromaSemanticMemory` sin cambiar el orchestrator.

## Config

```yaml
memory:
  enabled: true
  short_term_turns: 20
  persistent_provider: sqlite
  semantic_provider: chroma
  semantic_enabled: true
  embedding_model: nomic-embed-text
```

Embeddings: `ollama pull nomic-embed-text`

## Prueba rápida

```bash
poetry run pytest tests/unit/test_memory.py
poetry run jarvis --once-text "Recuerda que mi nombre es Juan"
# reinicia
poetry run jarvis --once-text "Muéstrame mis notas"
```
