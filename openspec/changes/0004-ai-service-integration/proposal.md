# Change 0004: AI Service Integration

## Summary

Connect persisted projects and ideas to the FastAPI AI service so ProgresIA Studio can generate requirements and OpenSpec records from real project data.

## Motivation

The web app currently stores project, idea and specification records, but the "OpenSpec" creation path is still a local baseline payload. The MVP needs a real service boundary from API to AI service before adding queues, multi-agent orchestration or generated artifacts.

## Scope

This change covers:

- NestJS API client for the FastAPI AI service.
- API endpoint to generate an OpenSpec specification for a project.
- Mapping from persisted `Project`/`Idea` to AI service `IdeaRequest`.
- Persistence of generated OpenSpec result in `Specification`.
- Frontend action to trigger generation through the API.

This change does not cover:

- BullMQ background jobs.
- Streaming progress.
- LLM provider calls.
- RAG indexing.
- Generated code artifacts.

## Impact

- Users can save an idea and generate a structured OpenSpec record from the AI service.
- Future queue-based generation can reuse the same service boundary.
- The AI service remains deterministic until LLM provider configuration is introduced.
