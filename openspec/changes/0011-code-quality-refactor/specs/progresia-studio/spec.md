# Delta: Code Quality Refactor

## ADDED Requirements

### Requirement: Deterministic Code Generation

The AI service SHALL support code generation without contacting an LLM provider when deterministic generation is explicitly requested.

#### Scenario: Caller disables LLM generation

- **GIVEN** a valid code generation request
- **WHEN** the caller invokes the code generation agent with `llm=None`
- **THEN** no provider SHALL be resolved or contacted
- **AND** the matching fallback scaffold SHALL be returned.

### Requirement: Validated LLM Runtime Configuration

The platform SHALL validate provider priority and model overrides before updating runtime routing.

#### Scenario: Administrator changes cloud priority

- **GIVEN** an authenticated administrator
- **WHEN** they submit a cloud provider order
- **THEN** the order SHALL contain Groq, OpenAI and Gemini exactly once
- **AND** blank model names SHALL be rejected.

### Requirement: Executable Fallback Scaffolds

Every registered fallback stack SHALL produce a coherent file set.

#### Scenario: A fallback builder generates a project

- **GIVEN** one of the registered fallback architectures
- **WHEN** deterministic generation runs
- **THEN** the result SHALL contain a README and environment example
- **AND** file paths SHALL be unique
- **AND** referenced runtime modules and dependencies SHALL be included.
