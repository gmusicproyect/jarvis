# Fase 4 completada — RAG + LlamaIndex

**Fecha:** 2026-07-27  
**Estado:** Completa (pendiente de tu OK antes de Fase 5)

## Objetivo

Sistema RAG profesional con proveedores intercambiables, indexación incremental, citas y rechazo cuando no hay evidencia.

## Arquitectura

```
DocumentLoader → Chunker → EmbeddingProvider → VectorStoreProvider
                                      ↓
                               Retriever → RAGOrchestrator → LLM
```

| Proveedor | Implementación |
|-----------|----------------|
| DocumentLoader | `CompositeLoader` (PDF, DOCX, TXT/MD, CSV, Excel, PPTX, JSON/YAML, código) |
| Chunker | LlamaIndex `SentenceSplitter` (fallback sliding window) |
| EmbeddingProvider | Ollama `nomic-embed-text` + caché SQLite |
| VectorStoreProvider | Chroma (`data/chroma_rag`, collection `jarvis_docs`) |
| Retriever | similitud coseno |
| RAGOrchestrator | contexto + citas + refuse |

Indexador: `IncrementalIndexer` (hash/mtime, paralelo, DB `data/db/rag_index.db`).  
Watcher opcional: `poetry run jarvis watch`.

## CLI (criterios de aceptación)

```bash
poetry run jarvis index                 # knowledge/
poetry run jarvis index ~/Documents
poetry run jarvis index --force
poetry run jarvis ask "¿Qué dice el manual sobre la instalación?"
poetry run jarvis watch                 # observa knowledge/
```

También por voz/skills: `AskDocsSkill` (“qué dice el manual…”, “dónde aparece Kubernetes…”).

## Config (`config.yaml` → `rag:`)

- `chunk_size` / `chunk_overlap`
- `top_k` / `min_score`
- `cache_embeddings` / `parallel_workers`
- `refuse_if_insufficient: true`
- `use_llamaindex_splitter: true`

## Memoria de sesión

`RAGOrchestrator.session_cache` evita re-retrieves idénticos en la misma sesión de voz (`Orchestrator._rag_session_cache`).

## Demo incluida

`knowledge/manual-instalacion.md` (instalación, vacaciones, Kubernetes).

## Dependencias nuevas

`llama-index-core`, `pypdf`, `python-docx`, `openpyxl`, `python-pptx`, `watchdog`.

## Verificación

```bash
poetry install
ollama pull nomic-embed-text
poetry run pytest tests/unit/test_rag.py -q
poetry run jarvis index
poetry run jarvis ask "¿Qué dice el manual sobre vacaciones?"
```

## Siguiente

Tras tu aprobación → **Fase 5** (automatización OS) con contexto documental disponible.
