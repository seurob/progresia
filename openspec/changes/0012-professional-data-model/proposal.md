# Proposal: Professional Generated Data Model

## Why

Generated projects currently receive useful domain tables, but the deterministic
fallback omits common production concerns such as session revocation, role
assignment, audit history, composite access indexes and explicit lifecycle
fields. This makes the first generated schema look simpler than the application
it is intended to support.

## What Changes

- Generate authentication, RBAC and audit tables when authentication is enabled.
- Generate richer domain tables with ownership, lifecycle, optimistic locking,
  metadata and soft deletion.
- Declare explicit foreign keys, deletion policies, indexes and uniqueness rules.
- Preserve a proportional MVP scope: no unrelated billing, notification or
  analytics tables are added automatically.
- Ensure Prisma fallback schemas remain executable and validate successfully.

## Non-Goals

- Inferring a complete industry-specific ERP schema from a short idea.
- Replacing architecture-specific ORM conventions.
- Adding tables without a functional or operational responsibility.
