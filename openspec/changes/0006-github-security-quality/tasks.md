# Tasks

- [x] Add CodeQL workflow.
- [x] Add Dependency Review workflow.
- [x] Add OpenSSF Scorecard workflow.
- [x] Add Dependabot configuration.
- [x] Add Security Policy.
- [x] Add GitHub agent issue template.
- [x] Add repository security configuration script.
- [x] Apply available repository security settings through GitHub API.
- [x] Seed labels and issues remotely.

## Remote Settings Notes

- Enabled vulnerability alerts.
- Enabled automated security fixes.
- Restricted default Actions workflow permissions to read.
- Advanced Security was rejected because it is not available for the current repository plan.
- Branch protection was rejected because it requires GitHub Pro or a public repository.
- CodeQL is skipped while the repository is private and code scanning is unavailable.
- Dependency Review and Scorecard are configured as non-blocking when GitHub plan support is unavailable.

## Validation

- [x] `npm run openspec:check`
- [x] `npm run lint`
- [x] `npm run typecheck`
- [x] `npm run test`
- [x] `npm run build`
