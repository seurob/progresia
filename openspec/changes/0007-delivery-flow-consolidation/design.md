# Design: Delivery Flow Consolidation

## Runtime Flow

1. User saves idea intake on a project.
2. User queues requirements or OpenSpec generation.
3. API stores a BullMQ job and returns `jobId`.
4. Frontend polls `GET /api/jobs/:jobId`.
5. Processor invokes the relevant domain service.
6. Domain service persists results and advances project status.
7. User generates an artifact bundle and code.
8. User downloads ZIP directly, requests a MinIO signed URL, or pushes generated files to GitHub.

## Project Status

- `DRAFT`: project created or idea being edited.
- `SPEC_READY`: OpenSpec generated.
- `GENERATED`: generated code persisted in an artifact bundle.
- `DEPLOYED`: generated files pushed to GitHub.

## Job Boundary

The API queues long-running AI actions instead of blocking the browser request:

- `generate-requirements`
- `generate-openspec`
- `generate-code`

Polling is the first progress mechanism. SSE can be introduced later without changing the core queue contract.

## Storage Boundary

Direct ZIP download remains available for local workflows. MinIO signed URLs provide the production-oriented path and keep generated files out of application memory after export.

## Security Boundary

Refresh tokens are stored hashed and rotated. GitHub personal tokens supplied for publication are used only for the current request and are not persisted.
