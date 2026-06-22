# Tasks

- [x] Create OpenSpec change for refactor stabilization.
- [x] Keep AI service env example aligned with README setup.
- [x] Keep Prisma seed compatible with verified-account auth.
- [x] Separate theme context from provider to remove Fast Refresh warning.
- [x] Remove generated Python cache artifacts from the workspace.
- [x] Run OpenSpec validation.
- [x] Run Node lint and tests.
- [x] Run focused web/API type and build checks.

## Validation Notes

- `npm run typecheck` and `npm run build` still fail at `prisma generate` on Windows with an `EPERM` DLL rename error.
- Equivalent source checks passed with `npm run typecheck -w apps/web`, `npx tsc --noEmit -p apps/api/tsconfig.json`, `npm run build -w apps/web` and `npx nest build`.
- `python -m ruff check .` and `python -m pytest` pass for the AI service.

## Deferred

- [ ] Split very large frontend route files after the current worktree is committed.
- [ ] Replace Prisma `package.json#prisma` config with Prisma 7-ready config in a dedicated dependency migration.
- [ ] Investigate Windows Prisma DLL lock outside source refactor.
