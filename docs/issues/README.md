# GitHub Issues Backlog

GitHub CLI is not installed in the current environment and no `GH_TOKEN`/`GITHUB_TOKEN` is available, so issues cannot be created remotely from this machine yet.

This folder keeps the issue backlog in Markdown, mapped to OpenSpec changes. When GitHub auth is available, run:

```powershell
$env:GH_TOKEN="..."
node scripts/create-github-repo.mjs
git push -u origin main
node scripts/create-github-issues.mjs
```

Each issue should reference:

- OpenSpec change folder.
- Spec path.
- Expected outcome.
- Validation commands.
