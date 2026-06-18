# Design: GitHub Security And Quality Automation

## Files As Source Of Truth

Versioned repository files configure the repeatable parts:

- `.github/workflows/ci.yml`
- `.github/workflows/codeql.yml`
- `.github/workflows/dependency-review.yml`
- `.github/workflows/scorecard.yml`
- `.github/dependabot.yml`
- `.github/ISSUE_TEMPLATE/*`
- `.github/labels.yml`
- `SECURITY.md`

## API Settings

Some security settings live in GitHub repository configuration and require admin permissions. They are applied by `scripts/configure-github-security.mjs` using `GH_TOKEN` or `GITHUB_TOKEN`.

## Agent Workflow

GitHub/Copilot coding agents should receive issues with:

- a single objective,
- linked OpenSpec context,
- explicit constraints,
- validation commands.
