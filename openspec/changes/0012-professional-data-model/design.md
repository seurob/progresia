# Design

## Baseline Tables

Authenticated projects receive:

- `users`: identity, credentials, account lifecycle and optimistic version.
- `roles`: stable role catalog.
- `user_roles`: role assignments with assignment audit data.
- `refresh_tokens`: hashed sessions with expiry and revocation.
- `audit_logs`: immutable security and domain activity trail.

## Domain Tables

Each inferred business entity includes:

- UUID primary key.
- `user_id` ownership boundary when authentication exists.
- Slug, name, description and explicit status.
- JSON metadata for bounded extensibility.
- Optimistic version.
- Creation, update and soft-deletion timestamps.

## Integrity

- Foreign keys declare `CASCADE`, `RESTRICT` or `SET NULL`.
- Query-oriented composite indexes cover owner/status and owner/creation time.
- Join tables declare contextual uniqueness.
- Table and column names use stable snake_case mappings.
