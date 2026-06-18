# Change 0002: API Foundation

## Summary

Implement the first functional backend foundation for ProgresIA Studio.

## Motivation

The platform needs a real persistence and authorization base before the frontend wizard, assistant panel and AI generation flow can be connected safely. This change creates the minimum useful API surface for users, workspaces, projects, ideas and specifications.

## Scope

This change covers:

- Prisma setup for PostgreSQL.
- Initial domain models for User, Workspace, WorkspaceMember, Project, Idea and Specification.
- JWT authentication with register and login.
- Role and workspace membership primitives.
- Protected endpoints for current user, workspaces, projects, ideas and specifications.
- Swagger annotations for the new API surface.
- Basic tests for auth and domain services.

This change does not cover:

- Refresh tokens.
- Password reset.
- Billing or usage limits.
- BullMQ jobs.
- GitHub integration.
- Real AI orchestration from the main API.

## Impact

- Frontend work can authenticate and create real projects.
- The AI service can later receive persisted project context from the API.
- Future generated artifacts can be linked to `Project` and `Specification` records.
