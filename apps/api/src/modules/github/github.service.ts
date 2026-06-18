import { Injectable, UnauthorizedException } from "@nestjs/common";

export interface GitHubRepoInfo {
  fullName: string;
  htmlUrl: string;
  cloneUrl: string;
  defaultBranch: string;
}

export interface PushFilesResult {
  repoUrl: string;
  cloneUrl: string;
  commitSha: string;
}

export interface FileToCommit {
  path: string;
  content: string;
}

interface GitHubErrorBody {
  message?: string;
}

@Injectable()
export class GithubService {
  private readonly baseUrl = "https://api.github.com";

  private async request<T>(
    token: string,
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
      },
      body: body !== undefined ? JSON.stringify(body) : undefined
    });

    if (response.status === 401) {
      throw new UnauthorizedException("GitHub token is invalid or expired");
    }

    if (!response.ok) {
      const err = (await response.json().catch(() => ({}))) as GitHubErrorBody;
      throw new Error(`GitHub API ${method} ${path} → ${response.status}: ${err.message ?? response.statusText}`);
    }

    return response.json() as Promise<T>;
  }

  async createRepo(
    token: string,
    name: string,
    description: string,
    isPrivate: boolean
  ): Promise<GitHubRepoInfo> {
    const data = await this.request<{
      full_name: string;
      html_url: string;
      clone_url: string;
      default_branch: string;
    }>(token, "POST", "/user/repos", {
      name,
      description,
      private: isPrivate,
      auto_init: false
    });

    return {
      fullName: data.full_name,
      htmlUrl: data.html_url,
      cloneUrl: data.clone_url,
      defaultBranch: data.default_branch ?? "main"
    };
  }

  async pushInitialCommit(
    token: string,
    fullName: string,
    defaultBranch: string,
    files: FileToCommit[],
    message: string
  ): Promise<string> {
    const [owner, repo] = fullName.split("/");

    // 1. Create a blob for each file
    const blobs = await Promise.all(
      files.map(async (file) => {
        const blob = await this.request<{ sha: string }>(
          token,
          "POST",
          `/repos/${owner}/${repo}/git/blobs`,
          { content: Buffer.from(file.content).toString("base64"), encoding: "base64" }
        );
        return { path: file.path, sha: blob.sha, mode: "100644" as const, type: "blob" as const };
      })
    );

    // 2. Create tree
    const tree = await this.request<{ sha: string }>(
      token,
      "POST",
      `/repos/${owner}/${repo}/git/trees`,
      { tree: blobs }
    );

    // 3. Create commit (no parents — initial commit)
    const commit = await this.request<{ sha: string }>(
      token,
      "POST",
      `/repos/${owner}/${repo}/git/commits`,
      { message, tree: tree.sha, parents: [] }
    );

    // 4. Create the initial branch ref
    await this.request(token, "POST", `/repos/${owner}/${repo}/git/refs`, {
      ref: `refs/heads/${defaultBranch}`,
      sha: commit.sha
    });

    return commit.sha;
  }

  async pushFiles(
    token: string,
    name: string,
    description: string,
    isPrivate: boolean,
    files: FileToCommit[],
    commitMessage: string
  ): Promise<PushFilesResult> {
    const repo = await this.createRepo(token, name, description, isPrivate);
    const commitSha = await this.pushInitialCommit(
      token,
      repo.fullName,
      repo.defaultBranch,
      files,
      commitMessage
    );

    return { repoUrl: repo.htmlUrl, cloneUrl: repo.cloneUrl, commitSha };
  }
}
