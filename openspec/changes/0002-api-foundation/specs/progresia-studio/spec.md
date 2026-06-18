# ProgresIA Studio API Foundation Delta

## ADDED Requirements

### Requirement: User authentication

The API MUST allow a user to register and log in with email and password using JWT bearer authentication.

#### Scenario: User registers

- **GIVEN** a visitor provides a valid name, email and password
- **WHEN** they request `POST /api/auth/register`
- **THEN** the API creates a user, creates a default workspace membership and returns an access token plus safe user data

#### Scenario: User logs in

- **GIVEN** a registered user provides valid credentials
- **WHEN** they request `POST /api/auth/login`
- **THEN** the API returns an access token plus safe user data

#### Scenario: Invalid credentials are submitted

- **GIVEN** login credentials do not match a stored user
- **WHEN** the API validates the request
- **THEN** it rejects the request without revealing whether the email or password failed

### Requirement: Workspace-backed projects

Projects MUST belong to a workspace and be accessible only to workspace members.

#### Scenario: Owner creates a project

- **GIVEN** an authenticated Owner belongs to a workspace
- **WHEN** they request `POST /api/projects` with valid project data
- **THEN** the API creates the project inside that workspace

#### Scenario: User lists projects

- **GIVEN** an authenticated user belongs to one or more workspaces
- **WHEN** they request `GET /api/projects`
- **THEN** the API returns only projects from those workspaces

### Requirement: Idea intake persistence

The API MUST persist structured idea intake data for a project.

#### Scenario: Idea is saved

- **GIVEN** an authenticated workspace member has access to a project
- **WHEN** they request `POST /api/ideas`
- **THEN** the API stores problem, target users, sector, features, complexity and constraints for that project

### Requirement: Specification persistence

The API MUST persist generated specifications for a project.

#### Scenario: Specification is saved

- **GIVEN** an authenticated workspace member has access to a project
- **WHEN** they request `POST /api/specifications`
- **THEN** the API stores the specification type, status and structured content for that project

### Requirement: Protected current user endpoint

The API MUST expose a protected endpoint for retrieving the current authenticated user.

#### Scenario: Current user is requested

- **GIVEN** a valid bearer token
- **WHEN** a client requests `GET /api/users/me`
- **THEN** the API returns safe user profile data without password hash
