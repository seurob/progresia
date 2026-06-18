## ADDED Requirements

### Requirement: Delivery State Transitions

The platform SHALL update project status as generation and delivery milestones complete.

#### Scenario: OpenSpec is generated

- **GIVEN** a project has a saved idea
- **WHEN** OpenSpec generation completes successfully
- **THEN** the project status SHALL become `SPEC_READY`.

#### Scenario: Code is generated

- **GIVEN** a project has a generated OpenSpec
- **WHEN** generated code is persisted in an artifact bundle
- **THEN** the project status SHALL become `GENERATED`.

#### Scenario: Code is pushed to GitHub

- **GIVEN** an artifact bundle contains generated files
- **WHEN** the files are pushed to a GitHub repository
- **THEN** the project status SHALL become `DEPLOYED`.

### Requirement: Asynchronous AI Jobs

The platform SHALL queue long-running AI actions and expose their status to the frontend.

#### Scenario: User queues an AI action

- **GIVEN** an authenticated user has access to a project
- **WHEN** the user requests requirements, OpenSpec or code generation through the jobs API
- **THEN** the API SHALL return a `jobId`
- **AND** the frontend SHALL poll job status until completion or failure.

### Requirement: Requirements Review

The platform SHALL let users generate and review requirements before or alongside OpenSpec generation.

#### Scenario: Requirements are generated

- **GIVEN** a project has idea intake
- **WHEN** requirements generation completes
- **THEN** the API SHALL persist a `REQUIREMENTS` specification
- **AND** the frontend SHALL render functional, non-functional and user-story sections.

### Requirement: Artifact Delivery

The platform SHALL provide direct and storage-backed artifact export paths.

#### Scenario: Direct ZIP download

- **GIVEN** an authenticated user has access to an artifact bundle
- **WHEN** the user downloads the bundle
- **THEN** the API SHALL return a ZIP containing generated files or manifest-rendered placeholder files.

#### Scenario: Signed ZIP URL

- **GIVEN** an authenticated user has access to an artifact bundle
- **WHEN** the user requests a storage-backed export URL
- **THEN** the API SHALL upload the ZIP to MinIO
- **AND** return a signed URL with a limited TTL.

### Requirement: Refresh Token Rotation

The platform SHALL support refresh token rotation for authenticated sessions.

#### Scenario: Refresh token is valid

- **GIVEN** a user has a valid refresh token
- **WHEN** the token is submitted to the refresh endpoint
- **THEN** the API SHALL invalidate the previous token
- **AND** return a new access token and refresh token.

### Requirement: Generated Code GitHub Publication

The platform SHALL publish generated code to GitHub without storing user GitHub credentials.

#### Scenario: Bundle is pushed to GitHub

- **GIVEN** an artifact bundle contains generated files
- **WHEN** the user submits a GitHub token and repository name
- **THEN** the API SHALL create the repository and initial commit
- **AND** SHALL NOT persist the GitHub token.
