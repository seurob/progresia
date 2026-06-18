# [OpenSpec] GitHub security and quality automation

Labels: `openspec`, `devops`, `security`, `quality`, `github-agent`, `task`

OpenSpec change: `0006-github-security-quality`

Spec path: `openspec/changes/0006-github-security-quality/specs/progresia-studio/spec.md`

## Outcome

Manage the project through GitHub Issues and Actions with security and quality gates enabled.

## Tasks

- [x] Add CodeQL workflow.
- [x] Add Dependency Review workflow.
- [x] Add OpenSSF Scorecard workflow.
- [x] Add Dependabot configuration.
- [x] Add Security Policy.
- [x] Add GitHub agent issue template.
- [x] Apply available repository security settings through GitHub API.
- [x] Seed labels and issues remotely.

## Remote Settings Notes

- Enabled vulnerability alerts.
- Enabled automated security fixes.
- Restricted default Actions workflow permissions to read.
- Advanced Security was rejected because it is not available for the current repository plan.
- Branch protection was rejected because it requires GitHub Pro or a public repository.

## Validation

- [x] `npm run openspec:check`
- [x] `npm run lint`
- [x] `npm run typecheck`
- [x] `npm run test`
- [x] `npm run build`
