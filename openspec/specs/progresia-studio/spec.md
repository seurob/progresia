# ProgresIA Studio Platform Specification

## Purpose

ProgresIA Studio MUST provide a controlled path from business idea to deployable MVP. The platform MUST favor explicit specification, traceable agent decisions and reproducible delivery over unrestricted code generation.

## Requirements

### Requirement: Monorepo foundation

The repository MUST be organized as a professional monorepo with independent applications for the web client, main API and AI service.

#### Scenario: Developer opens the repository

- **GIVEN** a developer clones the repository
- **WHEN** they inspect the project root
- **THEN** they find `apps/web`, `apps/api`, `apps/ai-service`, `packages/shared`, `packages/contracts`, `packages/config`, `docs`, `infra`, `docker` and `scripts`

#### Scenario: Developer validates the workspace

- **GIVEN** dependencies are installed
- **WHEN** the developer runs `npm run lint`, `npm run typecheck`, `npm run test` and `npm run build`
- **THEN** the Node workspaces complete without blocking errors

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

#### Scenario: API documentation is requested

- **GIVEN** the API is running
- **WHEN** a client opens `/api/docs`
- **THEN** Swagger documentation is available for the exposed API

### Requirement: AI service contract

The AI service MUST expose deterministic baseline endpoints before integrating external LLM providers.

#### Scenario: AI service health is requested

- **GIVEN** the AI service is running
- **WHEN** a client requests `GET /health`
- **THEN** the response includes `status: ok` and `service: progresia-ai-service`

#### Scenario: Requirements are generated from an idea

- **GIVEN** a valid idea payload with project name, sector, problem, target users and core features
- **WHEN** a client requests `POST /generate-requirements`
- **THEN** the service returns functional requirements, non-functional requirements and user stories

#### Scenario: OpenSpec is generated from an idea

- **GIVEN** a valid idea payload
- **WHEN** a client requests `POST /generate-openspec`
- **THEN** the service returns a structured specification object linked to the project name

### Requirement: Specification-first development

Every substantial platform capability MUST be introduced through OpenSpec before implementation.

#### Scenario: New capability is proposed

- **GIVEN** a developer wants to add a substantial capability
- **WHEN** they start the work
- **THEN** they create a folder under `openspec/changes/` with `proposal.md`, `design.md`, `tasks.md` and at least one spec delta

#### Scenario: OpenSpec is validated

- **GIVEN** the repository has OpenSpec files
- **WHEN** the developer runs `npm run openspec:check`
- **THEN** the command verifies the required structure and fails on missing change artifacts

### Requirement: Generated MVP scope

The generated MVP kit MUST include a frontend, backend, database model, documentation and deployment assets for a controlled application pattern.

#### Scenario: User completes idea intake

- **GIVEN** an Owner has described a business idea
- **WHEN** the system completes product analysis, requirements and OpenSpec generation
- **THEN** the platform can prepare artifacts for frontend, backend, data model, Docker, tests and documentation

### Requirement: Role model

The platform MUST support the roles Admin, Owner, Collaborator and Reviewer as first-class authorization concepts.

#### Scenario: Role-sensitive capability is accessed

- **GIVEN** a user is authenticated
- **WHEN** the user performs a protected action
- **THEN** the API evaluates the action against the user's role and workspace permissions
