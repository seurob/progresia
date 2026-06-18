# Change: GitHub Security And Quality Automation

## Why

The repository needs GitHub-native project management and security feedback loops before the codebase grows further.

## What Changes

- Add security and quality GitHub Actions.
- Add Dependabot configuration.
- Add a security policy.
- Add a GitHub agent issue template.
- Add scripts to apply repository settings and seed issues when a token is available.

## Impact

- GitHub will run CI, CodeQL, Dependency Review and OpenSSF Scorecard.
- Dependabot will open dependency update pull requests.
- Issues can be seeded from the local OpenSpec-linked backlog.
