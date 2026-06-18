import { readFileSync } from "node:fs";
import { readdir } from "node:fs/promises";
import { basename, join } from "node:path";

const owner = "seurob";
const repo = "progresia";
const token = process.env.GH_TOKEN ?? process.env.GITHUB_TOKEN;
const labelDefinitions = [
  { name: "openspec", color: "0E8A16", description: "Work tied to an OpenSpec change." },
  { name: "backend", color: "1D76DB", description: "NestJS API, Prisma and backend domain work." },
  { name: "frontend", color: "5319E7", description: "React web application work." },
  { name: "ai-service", color: "FBCA04", description: "FastAPI, agents, RAG and LLM integration work." },
  { name: "devops", color: "C2E0C6", description: "Docker, CI/CD, deployment and infra." },
  { name: "docs", color: "0075CA", description: "Documentation, Obsidian and project knowledge." },
  { name: "task", color: "D4C5F9", description: "Implementation task." },
  { name: "security", color: "B60205", description: "Security hardening, scanning and vulnerability response." },
  { name: "quality", color: "5319E7", description: "Test, maintainability and quality gate improvements." },
  { name: "dependencies", color: "0366D6", description: "Dependency updates and dependency risk management." },
  { name: "github-agent", color: "7057FF", description: "Issue scoped for GitHub or Copilot coding agents." }
];

if (!token) {
  console.error("Missing GH_TOKEN or GITHUB_TOKEN.");
  process.exit(1);
}

const issueDir = join(process.cwd(), "docs", "issues");
const files = (await readdir(issueDir)).filter((file) => /^\d+-.+\.md$/.test(file));

async function githubFetch(path, options) {
  return fetch(`https://api.github.com/repos/${owner}/${repo}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "progresia-issue-seeder",
      ...options.headers
    }
  });
}

for (const label of labelDefinitions) {
  const response = await githubFetch("/labels", {
    method: "POST",
    body: JSON.stringify(label)
  });

  if (response.ok) {
    console.log(`label created: ${label.name}`);
    continue;
  }

  if (response.status !== 422) {
    const text = await response.text();
    throw new Error(`Failed to create label ${label.name}: ${response.status} ${text}`);
  }
}

for (const file of files) {
  const fullPath = join(issueDir, file);
  const content = readFileSync(fullPath, "utf8");
  const [titleLine, ...bodyLines] = content.split(/\r?\n/);
  const title = titleLine.replace(/^#\s*/, "").trim();
  const labelsLine = bodyLines.find((line) => line.startsWith("Labels:"));
  const labels = labelsLine
    ? [...labelsLine.matchAll(/`([^`]+)`/g)].map((match) => match[1])
    : ["openspec", "task"];

  const response = await githubFetch("/issues", {
    method: "POST",
    body: JSON.stringify({
      title,
      body: `${bodyLines.join("\n").trim()}\n\nSource: \`docs/issues/${basename(file)}\``,
      labels
    })
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to create issue from ${file}: ${response.status} ${text}`);
  }

  const issue = await response.json();
  console.log(`#${issue.number} ${issue.title}`);
}
