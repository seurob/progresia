const owner = "seurob";
const repo = "progresia";
const token = process.env.GH_TOKEN ?? process.env.GITHUB_TOKEN;

if (!token) {
  console.error("Missing GH_TOKEN or GITHUB_TOKEN.");
  process.exit(1);
}

const baseUrl = `https://api.github.com/repos/${owner}/${repo}`;
const headers = {
  Authorization: `Bearer ${token}`,
  Accept: "application/vnd.github+json",
  "X-GitHub-Api-Version": "2022-11-28",
  "User-Agent": "progresia-security-configurator"
};

async function githubFetch(path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers
    }
  });

  if (response.ok || response.status === 204) {
    return response;
  }

  const text = await response.text();
  throw new Error(`${options.method ?? "GET"} ${path} failed: ${response.status} ${text}`);
}

async function tryStep(name, fn) {
  try {
    await fn();
    console.log(`ok: ${name}`);
  } catch (error) {
    console.warn(`skip: ${name}`);
    console.warn(error instanceof Error ? error.message : error);
  }
}

await tryStep("enable vulnerability alerts", () =>
  githubFetch("/vulnerability-alerts", { method: "PUT" })
);

await tryStep("enable automated security fixes", () =>
  githubFetch("/automated-security-fixes", { method: "PUT" })
);

await tryStep("enable repository security analysis", () =>
  githubFetch("", {
    method: "PATCH",
    body: JSON.stringify({
      has_issues: true,
      has_projects: true,
      security_and_analysis: {
        advanced_security: { status: "enabled" },
        secret_scanning: { status: "enabled" },
        secret_scanning_push_protection: { status: "enabled" },
        dependabot_security_updates: { status: "enabled" }
      }
    })
  })
);

await tryStep("restrict default actions permissions", () =>
  githubFetch("/actions/permissions/workflow", {
    method: "PUT",
    body: JSON.stringify({
      default_workflow_permissions: "read",
      can_approve_pull_request_reviews: false
    })
  })
);

await tryStep("protect main branch", () =>
  githubFetch("/branches/main/protection", {
    method: "PUT",
    body: JSON.stringify({
      required_status_checks: null,
      enforce_admins: false,
      required_pull_request_reviews: {
        required_approving_review_count: 1,
        dismiss_stale_reviews: true,
        require_code_owner_reviews: false
      },
      restrictions: null,
      required_linear_history: true,
      allow_force_pushes: false,
      allow_deletions: false,
      block_creations: false,
      required_conversation_resolution: true,
      lock_branch: false,
      allow_fork_syncing: true
    })
  })
);

console.log("GitHub security and quality configuration completed.");
