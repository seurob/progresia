# Change: Delivery Flow Consolidation

## Why

Sprints H, I and J introduced the first end-to-end delivery flow: idea intake can now produce requirements, OpenSpec, generated code, downloadable ZIPs and optional GitHub publication. The behavior needs an explicit OpenSpec change so project state, async jobs and artifact delivery remain traceable.

## What Changes

- Project status transitions are applied when specifications, code and GitHub delivery complete.
- Requirements generation is available from the API and visible in the project UI.
- Long-running AI work is queued through BullMQ and exposed through job status polling.
- Artifact bundles can persist generated code.
- ZIP artifacts can be downloaded directly or uploaded to MinIO for a signed URL.
- Auth supports refresh token rotation.
- Generated code can be pushed to a new GitHub repository with a transient user token.

## Impact

- Extends Prisma with refresh tokens and generated artifact content.
- Adds API modules for jobs, storage and GitHub publication.
- Extends the AI service with code generation and task-aware LLM routing.
- Extends the web project detail workflow and test coverage.
