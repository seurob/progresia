# ProgresIA Studio Spec Delta

## MODIFIED Requirements

### Requirement: Specification-first development

Every substantial platform capability or broad maintenance pass MUST be introduced through OpenSpec before implementation.

#### Scenario: Refactor pass is proposed

- **GIVEN** the project needs a broad refactor or stabilization pass
- **WHEN** implementation starts
- **THEN** the repository contains an OpenSpec change describing scope, non-goals, validation and deferred work

### Requirement: Monorepo foundation

The repository MUST stay free of generated runtime cache artifacts in source directories.

#### Scenario: Generated cache files exist locally

- **GIVEN** Python runtime cache directories are generated during local execution
- **WHEN** the refactor pass runs
- **THEN** `__pycache__` and `.pyc` files are removed from source directories and remain covered by `.gitignore`
