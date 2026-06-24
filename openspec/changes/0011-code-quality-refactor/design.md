# Design: Code Quality Refactor

## Provider Adapters

FastAPI routes delegate provider model discovery to `ModelCatalogService`. The service owns HTTP timeouts, provider response normalization and safe fallbacks so route handlers remain transport-focused.

## Runtime Configuration

Pydantic validates provider names, model names and cloud priority as a complete permutation. Runtime state is copied while holding the configuration lock and provider factories operate from that snapshot.

## Deterministic Generation

`CodeGenerationAgent.generate()` distinguishes automatic provider resolution from an explicit `llm=None`. This lets jobs use configured providers while tests and deterministic callers bypass network access reliably.

## Fallback Scaffolds

The stack detector remains the source of truth for the 19 fallback builders. Beginner web projects use the Express TypeScript scaffold. Smoke tests verify stack selection, required files and unique paths.

## Frontend Boundaries

The AI settings page consumes typed API functions and focused model controls from `features/llm-config`, reducing route-level state and repeated request code.
