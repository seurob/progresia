# ProgresIA Studio Platform Delta

## ADDED Requirements

### Requirement: Monorepo foundation

The repository MUST be organized as a professional monorepo with independent applications for the web client, main API and AI service.

#### Scenario: Developer opens the repository

- **GIVEN** a developer clones the repository
- **WHEN** they inspect the project root
- **THEN** they find `apps/web`, `apps/api`, `apps/ai-service`, `packages/shared`, `packages/contracts`, `packages/config`, `docs`, `infra`, `docker` and `scripts`

### Requirement: Local infrastructure

The platform MUST provide a Docker Compose environment for the core infrastructure required by the MVP.

#### Scenario: Infrastructure starts locally

- **GIVEN** Docker is available
- **WHEN** the developer runs `docker compose up -d`
- **THEN** PostgreSQL, Redis, Qdrant and MinIO are available locally

### Requirement: API health and documentation

The main API MUST expose a health endpoint and generated OpenAPI documentation.

#### Scenario: API health is requested

- **GIVEN** the API is running
- **WHEN** a client requests `GET /api/health`
- **THEN** the response includes `status: ok`, `service: progresia-api` and a timestamp

### Requirement: AI service contract

The AI service MUST expose deterministic baseline endpoints before integrating external LLM providers.

#### Scenario: Requirements are generated from an idea

- **GIVEN** a valid idea payload with project name, sector, problem, target users and core features
- **WHEN** a client requests `POST /generate-requirements`
- **THEN** the service returns functional requirements, non-functional requirements and user stories

### Requirement: Specification-first development

Every substantial platform capability MUST be introduced through OpenSpec before implementation.

#### Scenario: New capability is proposed

- **GIVEN** a developer wants to add a substantial capability
- **WHEN** they start the work
- **THEN** they create a folder under `openspec/changes/` with `proposal.md`, `design.md`, `tasks.md` and at least one spec delta
