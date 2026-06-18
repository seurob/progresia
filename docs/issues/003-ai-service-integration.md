# [OpenSpec] Connect AI service to project workflow

Labels: `openspec`, `ai-service`, `backend`, `task`

OpenSpec change: `TBD-ai-service-integration`

Spec path: `openspec/changes/TBD-ai-service-integration/specs/progresia-studio/spec.md`

## Outcome

Connect persisted project and idea data to the FastAPI service so requirements and OpenSpec generation can be triggered from the web app.

## Tasks

- [ ] Create OpenSpec change before implementation.
- [ ] Add API endpoint to request requirements generation for a project.
- [ ] Call AI service from NestJS API.
- [ ] Persist generated requirements/specifications.
- [ ] Show generation result in project detail.
- [ ] Add tests for deterministic AI flow.

## Validation

- [ ] `npm run openspec:check`
- [ ] `npm run lint`
- [ ] `npm run typecheck`
- [ ] `npm run test`
- [ ] `npm run build`
- [ ] `python -m ruff check .`
- [ ] `python -m pytest`
