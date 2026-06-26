# [AI] Enable local Ollama models in production

Labels: `ai-service`, `devops`, `backend`, `task`

OpenSpec change: `openspec/changes/0007-delivery-flow-consolidation`

Spec path: `openspec/changes/0007-delivery-flow-consolidation/specs/progresia-studio/spec.md`

## Outcome

Install and run Ollama in production so ProgresIA can generate requirements, OpenSpec and code through local models.

## Context

Production is configured with `LLM_PROVIDER=ollama` and `OLLAMA_BASE_URL=http://ollama:11434`. Ollama runs as the `progresia-ollama` container in the production compose stack.

## Tasks

- [x] Install Ollama in the production compose stack.
- [x] Start the `progresia-ollama` container.
- [x] Pull balanced model for normal machines:
  - `ollama pull gemma4:26b-a4b-it-qat`
- [x] Pull higher-quality model for stronger RAM/GPU:
  - `ollama pull gemma4:31b`
- [x] Confirm `OLLAMA_BASE_URL=http://ollama:11434` works from `progresia-ai-service`.
- [x] Update AI settings default reasoning/code model if final model names differ from current `.env.production`.
- [ ] Run an AI smoke test through `/ai-settings` and project generation flow.
- [ ] Document expected RAM/GPU requirements and fallback behavior.

## Validation

- [x] `docker exec progresia-ollama ollama list`
- [x] `docker exec progresia-ai-service python -c "import urllib.request; print(urllib.request.urlopen('http://ollama:11434/api/tags').read()[:200])"`
- [x] `curl https://progresia.alumnes-monlau.com/api/health`
- [ ] Browser smoke test: `/ai-settings` lists local Ollama models.
- [ ] Browser smoke test: generated project uses local AI before template fallback.
