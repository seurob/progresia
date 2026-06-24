## ADDED Requirements

### Requirement: Complete Generated Project Package

The platform SHALL generate deliverables that include code, README, docs, SDD, setup guidance, infrastructure files and GitHub automation context.

#### Scenario: ZIP contains generated code and manifest-rendered support files

- **GIVEN** an artifact bundle contains generated code
- **WHEN** the user exports the ZIP
- **THEN** the ZIP SHALL include generated code
- **AND** SHALL include manifest-rendered documentation, SDD, setup and infrastructure files not already present in the generated code.

### Requirement: Pre-Download Summary

The platform SHALL show a final summary before artifact download.

#### Scenario: User reviews bundle summary

- **GIVEN** an artifact bundle exists
- **WHEN** the project detail page renders the bundle card
- **THEN** the user SHALL see project name, file count, stack, services, next steps, commands and cost notes.

### Requirement: GitHub Publication Completeness

The platform SHALL publish the same complete deliverable that ZIP export contains.

#### Scenario: Bundle is pushed to GitHub

- **GIVEN** an artifact bundle contains generated code
- **WHEN** the user publishes to GitHub
- **THEN** the commit SHALL include generated code and manifest-rendered support files.

### Requirement: Artifact Coherence Validation

The platform SHALL warn when generated artifacts appear incomplete or inconsistent.

#### Scenario: Validation checks documentation coherence

- **GIVEN** an artifact bundle exists
- **WHEN** validation runs
- **THEN** the platform SHALL check README presence, SDD presence, docs presence, environment example, Docker support, README-stack coherence, official documentation links and empty directory entries.

### Requirement: Specification PDF Export

The platform SHALL let users download generated specifications as PDF documents.

#### Scenario: User downloads OpenSpec PDF

- **GIVEN** an authenticated user has access to a generated specification
- **WHEN** they request PDF export
- **THEN** the API SHALL return an `application/pdf` document
- **AND** the project detail UI SHALL expose a download action from the OpenSpec card.

### Requirement: Generated README as Project Guide

The generated ZIP SHALL include a README that summarizes the project and explains how to run it locally.

#### Scenario: User opens the README from the ZIP

- **GIVEN** an artifact bundle has a generated `README.md`
- **WHEN** the user opens the README after downloading the ZIP
- **THEN** it SHALL describe the project purpose, MVP scope, stack, generated documentation and local services
- **AND** it SHALL include step-by-step startup commands for environment variables, Docker infrastructure, dependencies, migrations and development servers
- **AND** it SHALL include official documentation links for the detected technologies
- **AND** it SHALL adapt migration, seed, test, lint and build commands to the generated stack/template
- **AND** it SHALL explain Docker services, initial deployment steps and estimated external service costs.

### Requirement: Multiplatform Installation Documentation

The generated package SHALL include installation documentation for Windows, Linux and macOS in both technical docs and SDD setup context.

#### Scenario: User needs OS-specific setup instructions

- **GIVEN** an artifact bundle is generated
- **WHEN** the user opens the generated documentation
- **THEN** it SHALL include `docs/development/environment-setup.md`
- **AND** it SHALL include `docs/development/windows-setup.md`, `docs/development/linux-setup.md` and `docs/development/macos-setup.md`
- **AND** it SHALL include `sdd/setup/windows.md`, `sdd/setup/linux.md`, `sdd/setup/macos.md` and `sdd/setup/required-tools.md`
- **AND** each OS-specific guide SHALL include commands to install Git, Node.js, Docker and stack-specific tools such as Python or PHP/Composer.

### Requirement: Complete Docs Folder

The generated package SHALL include a complete `docs/` folder with product, architecture, development, API, AI and deployment documentation.

#### Scenario: User opens generated docs

- **GIVEN** an artifact bundle is generated
- **WHEN** the user inspects the `docs/` folder
- **THEN** it SHALL include product docs for idea, problem, target users, value proposition and MVP
- **AND** it SHALL include development docs for contributing, environment setup, OS setup, workflow and testing
- **AND** it SHALL include API docs for reference, endpoints, contract and authentication/authorization
- **AND** it SHALL include architecture docs for overview, entity relation diagram, architecture decisions and data model
- **AND** it SHALL include deployment docs for local development, Docker, production, environment variables, costs and deployment guide
- **AND** it SHALL include AI docs when the generated project includes an AI service or AI stack.

### Requirement: Complete SDD Folder

The generated package SHALL include a complete `sdd/` folder with dedicated specification, planning, task, prompt and setup files.

#### Scenario: User continues development with SDD

- **GIVEN** an artifact bundle is generated
- **WHEN** the user inspects the `sdd/` folder
- **THEN** it SHALL include `sdd/constitution.md`, `sdd/technology-decisions.md`, `sdd/non-functional-requirements.md` and `sdd/acceptance-criteria.md`
- **AND** it SHALL include requirements split into `requirements.md`, `user-stories.md`, `functional-requirements.md`, `non-functional-requirements.md` and `acceptance-criteria.md`
- **AND** it SHALL include `sdd/specifications/openspec.md` and at least one `feature-*.md` specification
- **AND** it SHALL include implementation, release, learning, backlog, initial tasks and task status files
- **AND** it SHALL include project context, resume, add-feature, fix-bug, code-review, testing and documentation prompts
- **AND** it SHALL include setup docs for environment, Windows, Linux, macOS and required tools.

### Requirement: AI Assistant Development Instructions

The generated package SHALL include actionable AI assistant instructions rather than placeholder stubs.

#### Scenario: User asks an AI assistant to continue development

- **GIVEN** an artifact bundle is generated
- **WHEN** the user opens `sdd/ai-development-instructions.md` or `sdd/prompts/ai-development-instructions.md`
- **THEN** the file SHALL include a mandatory 10-step SDD workflow
- **AND** it SHALL include restrictions for destructive changes, dependencies, secrets, migrations, stack changes, tests and unrelated refactors
- **AND** it SHALL include ready-to-use prompts for starting a session, implementing a feature and fixing a bug
- **AND** it SHALL include a closing checklist for verification and documentation updates.

### Requirement: Guided Intake Transparency

The project intake chat SHALL explain when the user is in a guided wizard and when downstream AI agents take over.

#### Scenario: User starts a new project

- **GIVEN** the user opens the new project page
- **WHEN** the first assistant message is shown
- **THEN** it SHALL describe the SDD workflow
- **AND** clarify that the first step is guided intake before AI generation.
