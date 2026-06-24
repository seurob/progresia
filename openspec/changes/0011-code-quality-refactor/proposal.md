# Proposal: Code Quality Refactor

## Why

The current implementation mixes provider discovery, runtime LLM routing and UI state in large modules. The fallback generator also contains stale tests from the retired sector-template system and several scaffolds were not fully executable.

## What Changes

- Separate LLM model catalog access from HTTP routes.
- Validate runtime provider configuration before applying it.
- Split the AI settings route into API, type and presentation modules.
- Make deterministic code generation explicit and prevent accidental Ollama calls.
- Align fallback tests with the current 19-stack generator.
- Repair generated NestJS and Flask authentication/runtime files.
- Keep Prisma generation resilient to the known Windows DLL lock.

## Non-Goals

- Redesigning the project wizard or generated artifact contract.
- Migrating Prisma major versions.
- Reintroducing retired sector-specific templates.
- Splitting every large route or generator in one change.
