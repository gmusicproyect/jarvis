# Fase 3 — Skills y herramientas

## Qué incluye

- `Skill` interface: `name`, `description`, `can_handle`, `execute`, `required_permissions`, `aliases`
- `SkillManager`: auto-descubrimiento builtin + plugins en `skills/`
- Router híbrido: reglas rápidas + LLM si hay ambigüedad (`HybridRouter`)
- Riesgo: `safe` | `confirm` | `restricted` (ej. `delete_file`)
- Observabilidad: logs `skill_selected` / `skill_executed` con `elapsed_ms`

## Skills iniciales

| Skill | Ejemplo |
|-------|---------|
| open_app | Abre Spotify |
| open_url | Abre https://openai.com |
| search_files | Busca el archivo presupuesto.pdf |
| read_text_file | Lee el archivo ~/nota.txt |
| datetime | ¿Qué hora es? |
| calculator | Calcula 12 + 5 |
| weather | ¿Qué clima hace? |
| news | Dame las noticias |
| timer | Pon un temporizador de 10 minutos |
| reminder | Recuérdame llamar a Carlos mañana |
| delete_file | Borra el archivo X (pide confirmación) |
| echo_plugin | `eco hola` (plugin dinámico) |

## Añadir skill sin tocar el núcleo

1. Crea `skills/mi_skill.py` con una clase que herede `Skill`
2. Reinicia Jarvis (`poetry run jarvis`)
3. El manager la carga solo

## Config

```yaml
skills:
  enabled: true
  plugin_dir: skills
  min_score: 0.55
  use_llm_router: true
  weather: { provider: open_meteo, latitude: 9.93, longitude: -84.08, city: "San José" }
  news: { rss_url: "...", limit: 3 }
```

## Pruebas

```bash
poetry run pytest tests/unit/test_skills.py tests/unit/test_skill_manager.py
```
