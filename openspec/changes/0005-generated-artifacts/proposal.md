# Change: Generated Artifact Bundles

## Why

ProgresIA Studio already captures an idea and generates an OpenSpec document. The next product step is to turn that specification into a persisted, reviewable artifact bundle so the user can see what files the future MVP kit will contain before code generation and ZIP export are implemented.

## What Changes

- Add a persisted artifact bundle concept connected to a project and source specification.
- Generate a deterministic manifest from the latest project OpenSpec.
- Expose API endpoints to generate and list artifact bundles.
- Surface artifact bundles in the project detail screen.

## Impact

- Adds a Prisma model and migration.
- Adds a new NestJS `artifacts` module.
- Extends project reads to include artifact bundles.
- Updates the frontend project detail workflow.
