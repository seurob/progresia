# ProgresIA Studio Delta

## ADDED Requirements

### Requirement: Professional baseline

When a generated project requires authentication, the OpenSpec SHALL include
identity, role assignment, refresh-token and audit-log tables in addition to
the business-domain tables.

### Requirement: Domain lifecycle

Generated mutable domain tables SHALL include ownership, status, optimistic
versioning, creation/update timestamps and soft deletion where appropriate.

### Requirement: Executable integrity

Generated ORM schemas SHALL include valid bidirectional relationships, explicit
foreign-key deletion behavior, table mappings and indexes for common access
patterns.
