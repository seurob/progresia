# [Security] Remediate Dependabot alerts

Labels: `security`, `dependencies`, `quality`, `task`

OpenSpec change: `TBD-dependency-alert-remediation`

Spec path: `TBD`

## Outcome

Resolve the current Dependabot alerts on the default branch without downgrading NestJS, Vite or the workspace toolchain.

## Current Alerts

- High: `multer` in `package-lock.json`
- Medium: `multer` in `package-lock.json`
- Medium: `js-yaml` in `package-lock.json`
- Low: `esbuild` in `package-lock.json`

## Tasks

- [ ] Review Dependabot PRs #1 to #7.
- [ ] Prefer upstream package updates over manual lockfile edits.
- [ ] Avoid `npm audit fix --force` if it downgrades framework majors.
- [ ] Keep CI green on `main`.
- [ ] Close or merge Dependabot PRs one by one.

## Validation

- [ ] `npm audit --omit=dev`
- [ ] `npm run lint`
- [ ] `npm run typecheck`
- [ ] `npm run test`
- [ ] `npm run build`
