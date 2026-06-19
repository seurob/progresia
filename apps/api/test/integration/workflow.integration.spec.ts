import { INestApplication, ValidationPipe } from "@nestjs/common";
import { Test } from "@nestjs/testing";
import * as request from "supertest";
import { Role } from "@prisma/client";
import * as bcrypt from "bcryptjs";
import { createHash } from "node:crypto";
import { AppModule } from "../../src/modules/app.module";
import { PrismaService } from "../../src/database/prisma.service";
import { AiServiceClient } from "../../src/modules/ai-service/ai-service.client";
import { GithubService } from "../../src/modules/github/github.service";

// Stable fixture data
const USER_ID      = "00000000-0000-4000-8000-000000000001";
const WORKSPACE_ID = "00000000-0000-4000-8000-000000000002";
const PROJECT_ID   = "00000000-0000-4000-8000-000000000003";
const SPEC_ID      = "00000000-0000-4000-8000-000000000004";
const PASSWORD = "change_me_123";

const dbUser = {
  id: USER_ID,
  email: "integration@progresia.local",
  name: "Integration User",
  passwordHash: bcrypt.hashSync(PASSWORD, 4),
  role: Role.OWNER,
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z")
};

const dbWorkspace = {
  id: WORKSPACE_ID,
  name: "Integration User's Workspace",
  ownerId: USER_ID,
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z"),
  members: [{ userId: USER_ID, role: Role.OWNER }]
};

const dbProject = {
  id: PROJECT_ID,
  workspaceId: WORKSPACE_ID,
  name: "Test App",
  sector: "Tech",
  productType: "Web App",
  description: "Integration test project",
  status: "DRAFT",
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z"),
  idea: null,
  specifications: [],
  artifactBundles: []
};

const dbIdea = {
  id: "int-idea-1",
  projectId: PROJECT_ID,
  problem: "Manual processes waste time",
  targetUsers: "Office workers",
  coreFeatures: ["Dashboard", "Reports"],
  complexity: "standard",
  needsAi: false,
  needsAuth: true,
  needsAdminPanel: false,
  constraints: null,
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z")
};

const dbSpec = {
  id: SPEC_ID,
  projectId: PROJECT_ID,
  type: "OPENSPEC",
  status: "GENERATED",
  content: { project: { name: "Test App" }, generatedBy: "ai-service" },
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z")
};

function buildPrismaMock(overrides: Record<string, unknown> = {}) {
  const refreshTokenHash = createHash("sha256").update("refresh-token").digest("hex");

  return {
    user: {
      findUnique: jest.fn(),
      findUniqueOrThrow: jest.fn().mockResolvedValue(dbUser),
      create: jest.fn().mockResolvedValue(dbUser)
    },
    workspace: {
      create: jest.fn().mockResolvedValue(dbWorkspace),
      findMany: jest.fn().mockResolvedValue([dbWorkspace]),
      findUnique: jest.fn().mockResolvedValue(dbWorkspace)
    },
    project: {
      create: jest.fn().mockResolvedValue(dbProject),
      findMany: jest.fn().mockResolvedValue([dbProject]),
      findUnique: jest.fn().mockResolvedValue({
        ...dbProject,
        workspace: dbWorkspace
      }),
      update: jest.fn().mockResolvedValue(dbProject)
    },
    idea: {
      upsert: jest.fn().mockResolvedValue(dbIdea),
      findUnique: jest.fn().mockResolvedValue(dbIdea)
    },
    specification: {
      create: jest.fn().mockResolvedValue(dbSpec),
      findMany: jest.fn().mockResolvedValue([dbSpec]),
      findFirst: jest.fn().mockResolvedValue(dbSpec)
    },
    artifactBundle: {
      create: jest.fn().mockResolvedValue(dbBundle),
      findMany: jest.fn().mockResolvedValue([dbBundle]),
      findFirst: jest.fn().mockResolvedValue(null),
      findUnique: jest.fn().mockResolvedValue(dbBundle),
      update: jest.fn().mockResolvedValue(dbBundle)
    },
    refreshToken: {
      create: jest.fn().mockResolvedValue({ id: "refresh-1" }),
      findUnique: jest.fn().mockResolvedValue({
        id: "refresh-1",
        userId: USER_ID,
        tokenHash: refreshTokenHash,
        expiresAt: new Date("2099-01-01T00:00:00Z")
      }),
      delete: jest.fn().mockResolvedValue({ id: "refresh-1" })
    },
    $transaction: jest.fn().mockImplementation((input: unknown) => {
      if (Array.isArray(input)) {
        return Promise.all(input);
      }

      const cb = input as (tx: unknown) => unknown;
      return cb({
        user: { create: jest.fn().mockResolvedValue(dbUser) },
        workspace: { create: jest.fn().mockResolvedValue(dbWorkspace) }
      });
    }),
    ...overrides
  };
}

const aiClientMock = {
  generateOpenSpec: jest.fn().mockResolvedValue({
    project_name: "Test App",
    spec: { project: { name: "Test App" }, requirements: [] }
  }),
  generateCode: jest.fn().mockResolvedValue({
    project_name: "Test App",
    files: [
      { path: "README.md", language: "markdown", content: "# Test" },
      { path: "docker-compose.yml", language: "yaml", content: "services: {}" }
    ]
  })
};

const githubServiceMock = {
  pushFiles: jest.fn().mockResolvedValue({
    repoUrl: "https://github.com/testuser/test-app",
    cloneUrl: "https://github.com/testuser/test-app.git",
    commitSha: "abc123"
  })
};

const BUNDLE_ID = "00000000-0000-4000-8000-000000000005";

const dbBundle = {
  id: BUNDLE_ID,
  projectId: PROJECT_ID,
  specificationId: SPEC_ID,
  status: "GENERATED",
  manifest: { version: "0.1.0", project: "Test App", files: [] },
  generatedContent: {
    project_name: "Test App",
    files: [
      { path: "README.md", language: "markdown", content: "# Test" },
      { path: "docker-compose.yml", language: "yaml", content: "services: {}" }
    ]
  },
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z"),
  project: {
    id: PROJECT_ID,
    name: "Test App",
    sector: "Tech",
    workspaceId: WORKSPACE_ID,
    workspace: { members: [{ userId: USER_ID, role: "OWNER" }] }
  }
};

describe("API workflow integration", () => {
  let app: INestApplication;
  let prismaMock: ReturnType<typeof buildPrismaMock>;

  beforeAll(async () => {
    prismaMock = buildPrismaMock();

    const moduleRef = await Test.createTestingModule({
      imports: [AppModule]
    })
      .overrideProvider(PrismaService)
      .useValue(prismaMock)
      .overrideProvider(AiServiceClient)
      .useValue(aiClientMock)
      .overrideProvider(GithubService)
      .useValue(githubServiceMock)
      .compile();

    app = moduleRef.createNestApplication();
    app.setGlobalPrefix("api");
    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
    await app.init();
  });

  afterAll(() => app.close());

  beforeEach(() => jest.clearAllMocks());

  // ── Auth ──────────────────────────────────────────────────────────────

  describe("POST /api/auth/register", () => {
    it("creates a user and returns accessToken", async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);

      const res = await request(app.getHttpServer())
        .post("/api/auth/register")
        .send({ name: "Integration User", email: "integration@progresia.local", password: PASSWORD });

      expect(res.status).toBe(201);
      expect(res.body).toHaveProperty("accessToken");
      expect(res.body.user).not.toHaveProperty("passwordHash");
    });

    it("rejects duplicate email with 409", async () => {
      prismaMock.user.findUnique.mockResolvedValue(dbUser);

      const res = await request(app.getHttpServer())
        .post("/api/auth/register")
        .send({ name: "Another", email: "integration@progresia.local", password: PASSWORD });

      expect(res.status).toBe(409);
    });

    it("rejects short password with 400", async () => {
      const res = await request(app.getHttpServer())
        .post("/api/auth/register")
        .send({ name: "Test", email: "test@progresia.local", password: "short" });

      expect(res.status).toBe(400);
    });
  });

  describe("POST /api/auth/login", () => {
    it("returns accessToken for valid credentials", async () => {
      prismaMock.user.findUnique.mockResolvedValue(dbUser);

      const res = await request(app.getHttpServer())
        .post("/api/auth/login")
        .send({ email: "integration@progresia.local", password: PASSWORD });

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty("accessToken");
    });

    it("returns 401 for wrong password", async () => {
      prismaMock.user.findUnique.mockResolvedValue(dbUser);

      const res = await request(app.getHttpServer())
        .post("/api/auth/login")
        .send({ email: "integration@progresia.local", password: "wrong_password" });

      expect(res.status).toBe(401);
    });

    it("returns 401 for unknown email", async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);

      const res = await request(app.getHttpServer())
        .post("/api/auth/login")
        .send({ email: "nobody@progresia.local", password: PASSWORD });

      expect(res.status).toBe(401);
    });
  });

  describe("POST /api/auth/refresh", () => {
    it("requires a refresh token", async () => {
      const res = await request(app.getHttpServer()).post("/api/auth/refresh");
      expect(res.status).toBe(400);
    });

    it("rotates a valid refresh token", async () => {
      const res = await request(app.getHttpServer())
        .post("/api/auth/refresh")
        .send({ refreshToken: "refresh-token" });

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty("accessToken");
      expect(res.body).toHaveProperty("refreshToken");
    });
  });

  // ── Authenticated helpers ─────────────────────────────────────────────

  async function getToken(): Promise<string> {
    prismaMock.user.findUnique.mockResolvedValue(dbUser);
    const res = await request(app.getHttpServer())
      .post("/api/auth/login")
      .send({ email: "integration@progresia.local", password: PASSWORD });
    return res.body.accessToken as string;
  }

  // ── Projects ──────────────────────────────────────────────────────────

  describe("POST /api/projects", () => {
    it("creates a project for a workspace member", async () => {
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .post("/api/projects")
        .set("Authorization", `Bearer ${token}`)
        .send({
          workspaceId: WORKSPACE_ID,
          name: "Test App",
          sector: "Tech",
          productType: "Web App",
          description: "Integration test project"
        });

      expect(res.status).toBe(201);
      expect(res.body.id).toBe(PROJECT_ID);
    });

    it("returns 401 without token", async () => {
      const res = await request(app.getHttpServer()).post("/api/projects").send({
        workspaceId: WORKSPACE_ID,
        name: "Test App",
        sector: "Tech",
        productType: "Web App",
        description: "x"
      });
      expect(res.status).toBe(401);
    });
  });

  describe("GET /api/projects", () => {
    it("lists projects for the authenticated user", async () => {
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .get("/api/projects")
        .set("Authorization", `Bearer ${token}`);

      expect(res.status).toBe(200);
      expect(Array.isArray(res.body)).toBe(true);
    });
  });

  // ── Ideas ─────────────────────────────────────────────────────────────

  describe("POST /api/ideas", () => {
    it("saves idea intake for a project", async () => {
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .post("/api/ideas")
        .set("Authorization", `Bearer ${token}`)
        .send({
          projectId: PROJECT_ID,
          problem: "Manual processes waste time",
          targetUsers: "Office workers",
          coreFeatures: ["Dashboard", "Reports"],
          needsAuth: true
        });

      expect(res.status).toBe(201);
      expect(res.body.projectId).toBe(PROJECT_ID);
    });
  });

  // ── Specifications ────────────────────────────────────────────────────

  describe("POST /api/specifications/project/:id/generate-openspec", () => {
    it("generates and persists OpenSpec from AI service", async () => {
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .post(`/api/specifications/project/${PROJECT_ID}/generate-openspec`)
        .set("Authorization", `Bearer ${token}`);

      expect(res.status).toBe(201);
      expect(res.body.id).toBe(SPEC_ID);
      expect(aiClientMock.generateOpenSpec).toHaveBeenCalledTimes(1);
    });

    it("returns 409 when project has no idea intake", async () => {
      prismaMock.idea.findUnique.mockResolvedValue(null);
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .post(`/api/specifications/project/${PROJECT_ID}/generate-openspec`)
        .set("Authorization", `Bearer ${token}`);

      expect(res.status).toBe(409);
    });
  });

  // ── Artifacts ─────────────────────────────────────────────────────────

  describe("POST /api/artifacts/:bundleId/push-to-github", () => {
    it("pushes generated code and returns repo URL", async () => {
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .post(`/api/artifacts/${BUNDLE_ID}/push-to-github`)
        .set("Authorization", `Bearer ${token}`)
        .send({ githubToken: "ghp_fake", repoName: "test-app" });

      expect(res.status).toBe(201);
      expect(res.body.repoUrl).toBe("https://github.com/testuser/test-app");
      expect(res.body.cloneUrl).toMatch(/\.git$/);
      expect(githubServiceMock.pushFiles).toHaveBeenCalledTimes(1);
    });

    it("returns 404 when bundle does not exist", async () => {
      prismaMock.artifactBundle.findUnique.mockResolvedValueOnce(null);
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .post(`/api/artifacts/${BUNDLE_ID}/push-to-github`)
        .set("Authorization", `Bearer ${token}`)
        .send({ githubToken: "ghp_fake", repoName: "test-app" });

      expect(res.status).toBe(404);
    });

    it("returns 409 when bundle has no generated code", async () => {
      prismaMock.artifactBundle.findUnique.mockResolvedValueOnce({
        ...dbBundle,
        generatedContent: null
      });
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .post(`/api/artifacts/${BUNDLE_ID}/push-to-github`)
        .set("Authorization", `Bearer ${token}`)
        .send({ githubToken: "ghp_fake", repoName: "test-app" });

      expect(res.status).toBe(409);
    });

    it("returns 400 for missing githubToken", async () => {
      const token = await getToken();

      const res = await request(app.getHttpServer())
        .post(`/api/artifacts/${BUNDLE_ID}/push-to-github`)
        .set("Authorization", `Bearer ${token}`)
        .send({ repoName: "test-app" });

      expect(res.status).toBe(400);
    });

    it("returns 401 without auth token", async () => {
      const res = await request(app.getHttpServer())
        .post(`/api/artifacts/${BUNDLE_ID}/push-to-github`)
        .send({ githubToken: "ghp_fake", repoName: "test-app" });

      expect(res.status).toBe(401);
    });
  });
});
