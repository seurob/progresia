# ProgresIA Studio AI Service Integration Delta

## ADDED Requirements

### Requirement: AI-backed OpenSpec generation

The API MUST generate an OpenSpec specification for a project by calling the AI service with persisted project and idea data.

#### Scenario: Project has idea intake

- **GIVEN** an authenticated user has access to a project
- **AND** the project has saved idea intake
- **WHEN** they request OpenSpec generation
- **THEN** the API calls the AI service
- **AND** persists a `Specification` record with type `OPENSPEC` and status `GENERATED`

#### Scenario: Project has no idea intake

- **GIVEN** an authenticated user has access to a project
- **AND** the project has no saved idea intake
- **WHEN** they request OpenSpec generation
- **THEN** the API rejects the request with a conflict error

### Requirement: Frontend generation action

The web app MUST expose a project detail action that triggers AI-backed OpenSpec generation.

#### Scenario: User generates OpenSpec

- **GIVEN** a user is viewing a project with saved idea intake
- **WHEN** they click the generation action
- **THEN** the web app calls the API generation endpoint and refreshes the specifications list
