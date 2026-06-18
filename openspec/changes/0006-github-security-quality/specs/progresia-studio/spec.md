## ADDED Requirements

### Requirement: GitHub Security Automation

The repository SHALL provide versioned GitHub Actions and Dependabot configuration for security and quality feedback.

#### Scenario: Pull request dependency review

- **GIVEN** a pull request changes dependency manifests
- **WHEN** GitHub Actions runs
- **THEN** Dependency Review SHALL check introduced dependencies
- **AND** the workflow SHALL fail for high severity vulnerabilities.

#### Scenario: Code scanning

- **GIVEN** code is pushed to `main`
- **WHEN** GitHub Actions runs
- **THEN** CodeQL SHALL analyze JavaScript, TypeScript and Python code.

#### Scenario: Agent-ready issue

- **GIVEN** a task can be delegated to a GitHub/Copilot coding agent
- **WHEN** an issue is created
- **THEN** the issue SHALL include objective, context, constraints and validation commands.
