const owner = "seurob";
const repo = "progresia";
const token = process.env.GH_TOKEN ?? process.env.GITHUB_TOKEN;

if (!token) {
  console.error("Missing GH_TOKEN or GITHUB_TOKEN.");
  process.exit(1);
}

const response = await fetch("https://api.github.com/user/repos", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "User-Agent": "progresia-repo-creator"
  },
  body: JSON.stringify({
    name: repo,
    private: false,
    description: "ProgresIA Studio: plataforma multiagente para transformar ideas de negocio en MVPs software desplegables.",
    has_issues: true,
    has_projects: true,
    has_wiki: false,
    auto_init: false
  })
});

if (response.ok) {
  const createdRepo = await response.json();
  console.log(`Repository created: ${createdRepo.html_url}`);
  process.exit(0);
}

if (response.status === 422) {
  console.log(`Repository ${owner}/${repo} may already exist.`);
  process.exit(0);
}

const text = await response.text();
throw new Error(`Failed to create repository: ${response.status} ${text}`);
