## ADDED Requirements

### Requirement: Artifact Bundle Manifest

The platform SHALL generate a persisted artifact bundle manifest for a project from its latest generated OpenSpec specification.

#### Scenario: Generate bundle from OpenSpec

- **GIVEN** an authenticated user has access to a project
- **AND** the project has a generated OpenSpec specification
- **WHEN** the user requests artifact bundle generation
- **THEN** the API SHALL persist an artifact bundle
- **AND** the bundle SHALL reference the source specification
- **AND** the manifest SHALL include entries for README, requirements, architecture and OpenSpec files.

#### Scenario: Reject bundle without OpenSpec

- **GIVEN** an authenticated user has access to a project
- **AND** the project has no generated OpenSpec specification
- **WHEN** the user requests artifact bundle generation
- **THEN** the API SHALL reject the request with a conflict response.
