# [AI] Enable local Ollama models in production

Labels: `ai-service`, `devops`, `backend`, `task`

OpenSpec change: `openspec/changes/0007-delivery-flow-consolidation`

Spec path: `openspec/changes/0007-delivery-flow-consolidation/specs/progresia-studio/spec.md`

## Outcome

Install and run Ollama on the production host so ProgresIA can generate requirements, OpenSpec and code through local models.

## Context

Production is configured with `LLM_PROVIDER=ollama` and `OLLAMA_BASE_URL=http://host.docker.internal:11434`, but the host still needs Ollama installed, running and populated with models.

## Tasks

- [ ] Install Ollama on the Ubuntu/Plesk server.
- [ ] Enable and start the Ollama service.
- [ ] Pull balanced model for normal machines:
  - `ollama pull gemma4:26b-a4b`
- [ ] Pull higher-quality model for stronger RAM/GPU:
  - `ollama pull gemma4:31b`
- [ ] Confirm `OLLAMA_BASE_URL=http://host.docker.internal:11434` works from `progresia-ai-service`.
- [ ] Update AI settings default reasoning/code model if final model names differ from current `.env.production`.
- [ ] Run an AI smoke test through `/ai-settings` and project generation flow.
- [ ] Document expected RAM/GPU requirements and fallback behavior.

## Validation

- [ ] `ollama list`
- [ ] `curl http://127.0.0.1:11434/api/tags`
- [ ] `docker exec progresia-ai-service python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').read()[:200])"`
- [ ] `curl https://progresia.alumnes-monlau.com/api/health`
- [ ] Browser smoke test: `/ai-settings` lists local Ollama models.
- [ ] Browser smoke test: generated project uses local AI before template fallback.
