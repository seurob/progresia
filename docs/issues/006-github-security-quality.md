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
- [ ] Apply repository security settings through GitHub API.
- [ ] Seed labels and issues remotely.

## Validation

- [x] `npm run openspec:check`
- [x] `npm run lint`
- [x] `npm run typecheck`
- [x] `npm run test`
- [x] `npm run build`
