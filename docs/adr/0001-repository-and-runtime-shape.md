# ADR 0001: Repository And Runtime Shape

## Status

Accepted

## Context

ProgresIA Studio contains multiple applications in one repository:

- React web app.
- NestJS API.
- FastAPI AI service.
- Shared packages.
- Docker Compose infrastructure.

The question is whether this should be treated as a monolith.

## Decision

The project is a **monorepo**, not a strict runtime monolith.

For the MVP, it can be managed like a single product delivery unit: one repository, one OpenSpec workflow, one CI pipeline and one local Docker environment. At runtime, however, it is already split into separate processes: frontend, API, AI service, PostgreSQL, Redis, Qdrant and MinIO.

The practical framing is:

- **Repository model:** monorepo.
- **Product governance:** monolithic MVP workflow.
- **Runtime model:** modular multi-service application.
- **Backend API internals:** pragmatic modular monolith until the domain needs stronger service boundaries.

## Consequences

- GitHub Issues should track work by OpenSpec change, not by app folder only.
- Architecture decisions should avoid premature microservice complexity.
- The AI service remains separate because Python/RAG/agent dependencies evolve differently from the NestJS API.
