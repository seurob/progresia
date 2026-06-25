# ProgresIA Studio Delta

## ADDED Requirements

### Requirement: AI-first technology decisions

The system SHALL try configured AI models in order before using the deterministic
technology catalog.

#### Scenario: First model fails

- **WHEN** the preferred model fails during invocation or returns an invalid architecture
- **THEN** the system tries the next configured AI model
- **AND** uses the deterministic catalog only after all AI models fail

### Requirement: AI-first code generation

The system SHALL try every configured code-capable AI before using a scaffold
template.

### Requirement: Ollama hardware profiles

The project SHALL document `gemma4:26b-a4b-it-qat` for balanced computers and
`gemma4:31b` for machines with a strong GPU or abundant RAM.

#### Scenario: Models are not installed yet

- **WHEN** the user opens AI settings before downloading Gemma 4
- **THEN** both recommended profiles remain visible and selectable
- **AND** the interface shows their installation commands and installation status
