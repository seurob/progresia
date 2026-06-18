# Change 0001: Initialize Platform Foundation

## Summary

Create the initial ProgresIA Studio platform foundation using a specification-first workflow.

## Motivation

The platform will become harder to evolve if implementation decisions happen before the product contract is explicit. This change establishes the base architecture, local infrastructure, service contracts and OpenSpec workflow before adding authentication, persistence, agents and generation flows.

## Scope

This change covers:

- Monorepo structure.
- Local infrastructure with PostgreSQL, Redis, Qdrant and MinIO.
- React web app shell.
- NestJS API shell with health and Swagger.
- FastAPI AI service shell with deterministic idea analysis/spec endpoints.
- OpenSpec project structure and validation command.

This change does not cover:

- Full authentication.
- Real LLM provider calls.
- Persistent project storage.
- ZIP export.
- GitHub repository creation.
- Cloud deployment.

## Impact

- Future work MUST update OpenSpec before code for substantial capabilities.
- CI can use `npm run openspec:check` as an early quality gate.
- Backend, frontend and AI service can evolve from stable contracts instead of ad hoc screens or endpoints.
