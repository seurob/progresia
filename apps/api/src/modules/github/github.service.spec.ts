import { UnauthorizedException } from "@nestjs/common";
import { GithubService } from "./github.service";

const FAKE_TOKEN = "ghp_faketoken123";
const FULL_NAME = "testuser/my-app";

function mockFetch(responses: Array<{ status: number; body: unknown }>) {
  let call = 0;
  return jest.fn().mockImplementation(() => {
    const { status, body } = responses[call++] ?? { status: 200, body: {} };
    return Promise.resolve({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(body),
      text: () => Promise.resolve(JSON.stringify(body))
    });
  });
}

describe("GithubService", () => {
  let service: GithubService;
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    service = new GithubService();
    originalFetch = global.fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe("createRepo", () => {
    it("creates a repo and maps the response", async () => {
      global.fetch = mockFetch([{
        status: 201,
        body: {
          full_name: FULL_NAME,
          html_url: "https://github.com/testuser/my-app",
          clone_url: "https://github.com/testuser/my-app.git",
          default_branch: "main"
        }
      }]);

      const result = await service.createRepo(FAKE_TOKEN, "my-app", "desc", false);

      expect(result.fullName).toBe(FULL_NAME);
      expect(result.htmlUrl).toBe("https://github.com/testuser/my-app");
      expect(result.defaultBranch).toBe("main");
    });

    it("throws UnauthorizedException on 401", async () => {
      global.fetch = mockFetch([{ status: 401, body: { message: "Bad credentials" } }]);

      await expect(service.createRepo(FAKE_TOKEN, "my-app", "desc", false))
        .rejects.toThrow(UnauthorizedException);
    });

    it("throws on other error status", async () => {
      global.fetch = mockFetch([{ status: 422, body: { message: "already exists" } }]);

      await expect(service.createRepo(FAKE_TOKEN, "my-app", "desc", false))
        .rejects.toThrow(/422/);
    });
  });

  describe("pushFiles", () => {
    it("makes 4 + N API calls (create repo, blobs, tree, commit, ref)", async () => {
      const fetchMock = mockFetch([
        // createRepo
        { status: 201, body: { full_name: FULL_NAME, html_url: "https://github.com/testuser/my-app", clone_url: "https://github.com/testuser/my-app.git", default_branch: "main" } },
        // blob for file 1
        { status: 201, body: { sha: "blob-sha-1" } },
        // blob for file 2
        { status: 201, body: { sha: "blob-sha-2" } },
        // create tree
        { status: 201, body: { sha: "tree-sha" } },
        // create commit
        { status: 201, body: { sha: "commit-sha" } },
        // create ref
        { status: 201, body: {} }
      ]);
      global.fetch = fetchMock;

      const result = await service.pushFiles(
        FAKE_TOKEN,
        "my-app",
        "description",
        false,
        [
          { path: "README.md", content: "# Hello" },
          { path: "docker-compose.yml", content: "services: {}" }
        ],
        "initial commit"
      );

      expect(result.commitSha).toBe("commit-sha");
      expect(result.repoUrl).toBe("https://github.com/testuser/my-app");
      expect(fetchMock).toHaveBeenCalledTimes(6);
    });
  });
});
