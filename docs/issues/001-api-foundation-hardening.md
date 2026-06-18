# [OpenSpec] Harden API foundation

Labels: `openspec`, `backend`, `task`

OpenSpec change: `0002-api-foundation`

Spec path: `openspec/changes/0002-api-foundation/specs/progresia-studio/spec.md`

## Outcome

Make the API foundation production-ready enough for the next MVP generation stages.

## Tasks

- [ ] Add refresh token strategy or document why it is deferred.
- [ ] Add integration tests for register, login, project, idea and specification flows.
- [ ] Add validation for project ownership edge cases.
- [ ] Add Prisma seed for demo data.
- [ ] Review dependency audit and document accepted risks.

## Validation

- [ ] `npm run openspec:check`
- [ ] `npm run lint`
- [ ] `npm run typecheck`
- [ ] `npm run test`
- [ ] `npm run build`
