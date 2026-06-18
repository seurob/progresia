# GitHub Issues Backlog

GitHub CLI is not installed in the current environment and no `GH_TOKEN`/`GITHUB_TOKEN` is available, so issues cannot be created remotely from this machine yet.

This folder keeps the issue backlog in Markdown, mapped to OpenSpec changes. When GitHub auth is available, run:

```powershell
$env:GH_TOKEN="..."
node scripts/create-github-repo.mjs
git push -u origin main
node scripts/configure-github-security.mjs
node scripts/create-github-issues.mjs
```

Remote issues seeded:

- #8 `[OpenSpec] Harden API foundation`
- #9 `[OpenSpec] Polish web foundation`
- #10 `[OpenSpec] Connect AI service to project workflow`
- #11 `[OpenSpec] Generate project artifacts`
- #12 `[OpenSpec] Maintain Obsidian project knowledge base`
- #13 `[OpenSpec] GitHub security and quality automation`

Each issue should reference:

- OpenSpec change folder.
- Spec path.
- Expected outcome.
- Validation commands.
