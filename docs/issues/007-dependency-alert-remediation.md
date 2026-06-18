# [Security] Remediate Dependabot alerts

Labels: `security`, `dependencies`, `quality`, `task`

OpenSpec change: `openspec/changes/0006-github-security-quality`

Spec path: `openspec/changes/0006-github-security-quality/specs/progresia-studio/spec.md`

## Outcome

Resolve the current Dependabot alerts on the default branch without downgrading NestJS, Vite or the workspace toolchain.

## Current Alerts

- High: `multer` via `@nestjs/platform-express@11.1.27`.
- Moderate: `js-yaml` via `@nestjs/swagger@11.4.4`.
- Resolved: `esbuild` by making `packages/config` resolve Vitest against Vite 8.

## Notes

- `npm audit fix` does not apply a safe fix for the remaining production alerts.
- `npm audit fix --force` proposes incompatible downgrades (`@nestjs/core@7.5.5` and `@nestjs/swagger@5.2.1`), so the remaining alerts are tracked as upstream-blocked.
- The API currently exposes no file-upload route, which limits practical exposure to the `multer` advisories while waiting for a safe NestJS update.

## Tasks

- [ ] Review Dependabot PRs #1 to #7 and replacement PR #15.
- [x] Merge Dependabot PR #1 (`actions/setup-python@6`).
- [x] Split safe updates from Dependabot PR #6 (`lucide-react`, `zod`, `class-validator`).
- [x] Track Prisma 7 and React Router 8 as separate migrations instead of merging PR #6 wholesale (#16, #17).
- [x] Prefer upstream package updates over manual lockfile edits.
- [x] Avoid `npm audit fix --force` if it downgrades framework majors.
- [x] Keep CI green on `main`.
- [ ] Close or merge Dependabot PRs one by one.

## Validation

- [x] `npm audit --omit=dev` documents remaining upstream-blocked NestJS/Swagger alerts.
- [x] `npm run lint`
- [x] `npm run typecheck`
- [x] `npm run test`
- [x] `npm run build`
- [x] `python -m ruff check .`
- [x] `python -m pytest`
