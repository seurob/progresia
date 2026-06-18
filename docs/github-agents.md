# GitHub Agents Workflow

Use GitHub/Copilot coding agents only for bounded issues with clear OpenSpec context and validation commands.

## Issue Shape

- One outcome per issue.
- Link the OpenSpec change folder.
- Link the relevant files.
- Include exact validation commands.
- Prefer implementation tasks that do not require product judgement.

## Labels

- `github-agent`: suitable for a GitHub/Copilot coding agent.
- `openspec`: behavior is governed by OpenSpec.
- `security`: security or quality gate work.
- `quality`: tests, lint, maintainability and reliability.

## Operating Rule

Humans keep ownership of architecture, product scope and review. Agents can draft code, tests and documentation from an issue.

If Copilot coding agent is enabled for the repository, assign an eligible issue to Copilot from GitHub after the issue is created.
