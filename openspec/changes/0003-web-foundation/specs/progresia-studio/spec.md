# ProgresIA Studio Web Foundation Delta

## ADDED Requirements

### Requirement: Authenticated web shell

The web app MUST provide login and register screens and protect product routes from unauthenticated users.

#### Scenario: Visitor opens the app

- **GIVEN** no access token is stored
- **WHEN** the visitor opens `/`
- **THEN** the app redirects them to `/login`

#### Scenario: User logs in

- **GIVEN** a registered user submits valid credentials
- **WHEN** the API returns an access token
- **THEN** the app stores the token and navigates to the dashboard

### Requirement: Dashboard

The web app MUST show the authenticated user's workspace and project overview.

#### Scenario: User opens dashboard

- **GIVEN** a valid bearer token
- **WHEN** the user opens `/`
- **THEN** the app displays current user, workspaces and visible projects

### Requirement: Project creation

The web app MUST allow an authenticated user to create a project in an accessible workspace.

#### Scenario: User creates project

- **GIVEN** the user belongs to at least one workspace
- **WHEN** they submit the project creation form
- **THEN** the app creates the project through the API and navigates to its detail page

### Requirement: Idea wizard

The web app MUST allow structured idea intake to be saved for a project.

#### Scenario: User saves idea intake

- **GIVEN** the user has access to a project
- **WHEN** they submit problem, target users, features and options
- **THEN** the app stores the idea through the API and refreshes the project detail view

### Requirement: Specification visibility

The web app MUST show stored specifications for a project and allow creating a baseline OpenSpec record.

#### Scenario: User creates baseline specification

- **GIVEN** a project exists
- **WHEN** the user creates a baseline specification from the project detail page
- **THEN** the app persists a specification record and displays it in the specifications list
