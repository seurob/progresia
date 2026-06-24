# Design: Generated Project Compliance

## Manifest-First Delivery

The artifact manifest is treated as the canonical list of files that should exist in the deliverable. When code generation is present, generated files override manifest-rendered placeholders by path.

## Rendered Documentation

New documentation files are rendered from OpenSpec source summary fields:

- project description and target users,
- modules,
- stack constraints,
- requirements,
- API endpoints,
- data model.

This keeps the generated ZIP educational and useful even when the AI service returns a partial scaffold.

## Pre-Download Summary

The API exposes a rich summary endpoint for stack, services, prerequisites, costs, quickstart commands and next steps. The frontend displays this before the ZIP action.

## Validation

Validation remains non-blocking for warnings but blocks export on critical issues:

- dangerous paths,
- duplicate paths,
- likely secrets.

Warnings cover documentation gaps and README/stack coherence.
