# Design: Initialize Platform Foundation

## Architecture

The repository is organized as a monorepo:

- `apps/web`: React client and product UI.
- `apps/api`: NestJS API for auth, users, workspaces, projects, specifications, jobs and artifacts.
- `apps/ai-service`: FastAPI service for agents, RAG and specification generation.
- `packages/shared`: shared primitives.
- `packages/contracts`: cross-service request/response contracts.
- `packages/config`: shared static configuration.

## Decisions

### Use deterministic AI endpoints before LLM integration

The AI service starts with deterministic agents so API contracts and tests can stabilize before adding OpenAI, Gemini or Ollama.

### Keep OpenSpec in-repo

OpenSpec lives in `openspec/` so product intent, implementation changes and technical contracts are versioned with the code.

### Validate structure with a local script

A small validator in `scripts/validate-openspec.mjs` checks the mandatory OpenSpec structure without depending on a global CLI.

### Publish Redis on 6380 by default

Redis uses container port `6379` and host port `6380` by default to avoid conflicts with an existing local Redis service.

## Risks

- Some dependency advisories are transitive and require upstream package updates or breaking changes.
- The initial AI endpoints are deterministic placeholders and do not yet represent true multiagent reasoning.
- OpenSpec discipline must be enforced in review or CI to remain useful.
