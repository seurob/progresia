# Design: API Foundation

## Domain Model

- `User`: account identity, credentials and global role.
- `Workspace`: team or personal scope for projects.
- `WorkspaceMember`: user membership and role inside a workspace.
- `Project`: business idea container.
- `Idea`: structured intake data for a project.
- `Specification`: generated or edited spec for a project.

## API Shape

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/me`
- `POST /api/workspaces`
- `GET /api/workspaces`
- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/:id`
- `PUT /api/projects/:id`
- `POST /api/ideas`
- `GET /api/ideas/project/:projectId`
- `POST /api/specifications`
- `GET /api/specifications/project/:projectId`

## Authorization

The first iteration uses JWT bearer authentication. Workspace access is enforced in services by checking membership or project ownership. Global roles remain available for future Admin and Reviewer workflows.

## Password Storage

Passwords are hashed with bcrypt before persistence. Plain passwords MUST NOT be returned from API responses.

## Error Handling

Services use NestJS HTTP exceptions for duplicate accounts, invalid credentials and missing resources.

## Testing

Unit tests should cover password hashing/login behavior and service-level domain operations where possible without a real database.
