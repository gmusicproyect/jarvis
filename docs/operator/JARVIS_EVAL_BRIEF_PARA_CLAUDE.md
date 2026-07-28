# Evaluación completa pre-DMG — Jarvis 1.0.0-rc.1

## Pedido del operador
NO instalar / NO validar DMG hasta que Claude revise el código y diga si está listo.
Quiere evaluación completa: instalador, voz, GUI, hardening, checklist, secretos, gates.

## Cómo revisar (GitHub web_fetch está en caché stale)
Adjuntar: `~/Desktop/jarvis-eval-3fdb8f9.tar.gz` (git archive de HEAD).
Descomprimir y auditar el árbol, no confiar en la página web de GitHub.

```bash
mkdir -p /tmp/jarvis-eval && tar -xzf ~/Desktop/jarvis-eval-3fdb8f9.tar.gz -C /tmp/jarvis-eval
```

## Estado git (fuente de verdad)
| Campo | Valor |
|-------|--------|
| HEAD local | **3fdb8f9** — fix(tts): ResilientTTS acepta cancel_flag |
| origin/main | **701615d** (local ahead 1 — TTS fix aún no pusheado) |
| Archivos tracked | 222 |
| Secretos en índice | `.env` ignorado; solo `.env.example` (placeholders) + `secrets.py` (código Keychain) |

## DMG vs código (CRÍTICO)
| Campo | Valor |
|-------|--------|
| DMG actual checklist | sha256 **d1cc8cbc…** ancla **2b1ea98** |
| ¿Incluye fix TTS 3fdb8f9? | **NO** |
| Conclusión | Instalar ese DMG hoy **reproduce el bug de voz** (no hay respuesta hablada). Hay que regenerar DMG desde 3fdb8f9+ **después** de que la eval de código diga OK. |

## Bugs encontrados en sesión de validación (ya corregidos en código)
1. **P0-3** Install RO: `mkdir .runtime` en volumen DMG → fix `bbffcb3` (copia a App Support).
2. **P0-4** `.app` kLSNoExecutableErr / sin python.path → fix `2b1ea98`.
3. **P0-5** Voz sin continuidad/respuesta: `ResilientTTS.speak() got unexpected keyword cancel_flag` → fix **`3fdb8f9`**. Evidencia en log:
   `turn_failed` / TypeError cancel_flag tras STT OK.
4. followup_seconds subido 6→12 en config (mismo commit).

## Hallazgos abiertos (no bloquean eval de código, sí el release)
- P1-2 DMG bootstrap (necesita red)
- P1-3 cobertura ~49%
- P1-5 cold-start sin Ollama/Homebrew no verificado (Camino B)
- CLEAN_MAC_CHECKLIST: PENDING (ningún PASS fresco sobre artefacto que incluya 3fdb8f9)
- tag v1.0.0 / Fase 10: BLOQUEADOS
- Firma/notarización: opcional PENDING

## Qué debe cubrir la evaluación de Claude
1. **Secretos / privacidad**: nada sensible en el árbol del archive.
2. **Instalador**: `scripts/install_standalone_macos.sh`, `create_dmg.sh`, `create_app_bundle.sh`, `Install.command` — ¿sobrevive DMG RO? ¿pin python.path? ¿CLI en ~/.local/bin?
3. **Voz E2E**: orchestrator → wake → STT → LLM → ResilientTTS(cancel_flag) → followup. ¿El fix 3fdb8f9 es completo? ¿wake score 0.0 en logs es síntoma aparte?
4. **GUI**: start_voice manual, tray, onboarding.
5. **Health/doctor**: Vision degraded = PASS base; no mentir P0-2.
6. **Hardening**: ErrorHandler, ResilientTTS, secrets module.
7. **Release gates**: ¿se puede generar DMG nuevo? ¿qué falta antes de checklist PASS?
8. **Riesgos residuales** con severidad P0/P1/P2 y veredicto: **LISTO para regen DMG** / **NO LISTO** + lista de fixes.

## Veredicto esperado (formato)
```
VEREDICTO: LISTO | NO LISTO para regenerar DMG
P0 abiertos: …
P1 abiertos: …
Acción siguiente obligatoria: …
Prohibido: tag v1.0.0, afirmar PASS de Mac limpio
```

## Evidencia local ya tomada (no sustituye code review)
- Unit tests: correr en máquina del operador (pytest necesita poetry env con cov o `-o addopts=`).
- `bash -n` scripts install/create_dmg/create_app/capture: OK
- Mic default OK; TTS smoke post-fix: speak_ok con cancel_flag
- install_scripts_syntax=OK

## Repo público
https://github.com/gmusicproyect/jarvis — preferir el tar.gz adjunto por caché web stale.

## Evidencia tests (2026-07-28)
`poetry run pytest tests/unit/ -q -o addopts=` → **76 passed** (4 warnings pydantic/chromadb). Incluye test nuevo cancel_flag en ResilientTTS.
