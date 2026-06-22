# Design: Codebase Refactor Stabilization

## Constraints

- Do not change frameworks, database, runtime architecture or public API contracts.
- Prefer local, low-risk changes over broad rewrites while the repository has many pending edits.
- Avoid deleting documentation, OpenSpec files, tests or templates unless they are proven obsolete.

## Refactor Strategy

1. Start from validation and lint signals.
2. Fix issues with the smallest change that improves maintainability.
3. Keep generated files out of the source tree.
4. Record blockers that are environmental rather than code defects.

## Known Non-Goals

- No RAG implementation in this refactor pass.
- No large component split for `NewProjectPage` or `ProjectDetailPage` until the current worktree is committed.
- No dependency major upgrades in this pass.
