import { ForbiddenException, NotFoundException } from "@nestjs/common";
import { Role } from "@prisma/client";
import { ProjectsService } from "./projects.service";

const OWNER_ID = "user-owner";
const OTHER_ID = "user-other";
const WORKSPACE_ID = "ws-1";
const PROJECT_ID = "project-1";

const project = {
  id: PROJECT_ID,
  name: "My App",
  sector: "Tech",
  productType: "Web App",
  description: "Test project",
  status: "DRAFT",
  workspaceId: WORKSPACE_ID,
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z"),
  workspace: {
    id: WORKSPACE_ID,
    members: [{ userId: OWNER_ID, role: Role.OWNER }]
  }
};

function buildMocks(projectOverride?: Partial<typeof project> | null) {
  const resolvedProject =
    projectOverride === null ? null : { ...project, ...projectOverride };

  const prisma = {
    project: {
      findUnique: jest.fn().mockResolvedValue(resolvedProject),
      create: jest.fn().mockResolvedValue({ ...project, workspace: undefined }),
      findMany: jest.fn().mockResolvedValue([{ ...project, workspace: undefined }]),
      update: jest.fn().mockResolvedValue({ ...project, workspace: undefined }),
      delete: jest.fn().mockResolvedValue({ id: PROJECT_ID })
    }
  };

  const workspacesService = {
    ensureMember: jest.fn().mockResolvedValue({ id: WORKSPACE_ID })
  };

  return { prisma, workspacesService };
}

describe("ProjectsService — ownership", () => {
  describe("ensureProjectAccess", () => {
    it("grants access to a workspace member", async () => {
      const { prisma, workspacesService } = buildMocks();
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(service.ensureProjectAccess(PROJECT_ID, OWNER_ID)).resolves.toMatchObject({
        id: PROJECT_ID
      });
    });

    it("throws NotFoundException for unknown project", async () => {
      const { prisma, workspacesService } = buildMocks(null);
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(service.ensureProjectAccess("non-existent", OWNER_ID)).rejects.toBeInstanceOf(
        NotFoundException
      );
    });

    it("throws ForbiddenException when user is not a workspace member", async () => {
      const { prisma, workspacesService } = buildMocks({
        workspace: { id: WORKSPACE_ID, members: [] }
      });
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(service.ensureProjectAccess(PROJECT_ID, OTHER_ID)).rejects.toBeInstanceOf(
        ForbiddenException
      );
    });
  });

  describe("findOne", () => {
    it("returns the project with relations for the owner", async () => {
      const { prisma, workspacesService } = buildMocks();
      prisma.project.findUnique
        .mockResolvedValueOnce(project)
        .mockResolvedValueOnce({ ...project, idea: null, specifications: [], artifactBundles: [] });
      const service = new ProjectsService(prisma as never, workspacesService as never);

      const result = await service.findOne(OWNER_ID, PROJECT_ID);
      expect(result).toMatchObject({ id: PROJECT_ID });
    });

    it("throws ForbiddenException when another user tries to access the project", async () => {
      const { prisma, workspacesService } = buildMocks({
        workspace: { id: WORKSPACE_ID, members: [] }
      });
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(service.findOne(OTHER_ID, PROJECT_ID)).rejects.toBeInstanceOf(ForbiddenException);
    });
  });

  describe("update", () => {
    it("allows the owner to update the project", async () => {
      const { prisma, workspacesService } = buildMocks();
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(
        service.update(OWNER_ID, PROJECT_ID, { name: "Renamed App" })
      ).resolves.toMatchObject({ id: PROJECT_ID });
    });

    it("throws ForbiddenException when a non-member tries to update", async () => {
      const { prisma, workspacesService } = buildMocks({
        workspace: { id: WORKSPACE_ID, members: [] }
      });
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(
        service.update(OTHER_ID, PROJECT_ID, { name: "Hacked App" })
      ).rejects.toBeInstanceOf(ForbiddenException);
    });

    it("throws NotFoundException when project does not exist", async () => {
      const { prisma, workspacesService } = buildMocks(null);
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(
        service.update(OWNER_ID, "non-existent", { name: "x" })
      ).rejects.toBeInstanceOf(NotFoundException);
    });
  });

  describe("remove", () => {
    it("deletes the project for the owner", async () => {
      const { prisma, workspacesService } = buildMocks();
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(service.remove(OWNER_ID, PROJECT_ID)).resolves.toBeUndefined();
      expect(prisma.project.delete).toHaveBeenCalledWith({ where: { id: PROJECT_ID } });
    });

    it("throws ForbiddenException when a non-member tries to delete", async () => {
      const { prisma, workspacesService } = buildMocks({
        workspace: { id: WORKSPACE_ID, members: [] }
      });
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(service.remove(OTHER_ID, PROJECT_ID)).rejects.toBeInstanceOf(ForbiddenException);
      expect(prisma.project.delete).not.toHaveBeenCalled();
    });

    it("throws NotFoundException when project does not exist", async () => {
      const { prisma, workspacesService } = buildMocks(null);
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await expect(service.remove(OWNER_ID, "non-existent")).rejects.toBeInstanceOf(NotFoundException);
      expect(prisma.project.delete).not.toHaveBeenCalled();
    });
  });

  describe("create", () => {
    it("delegates workspace membership check to WorkspacesService", async () => {
      const { prisma, workspacesService } = buildMocks();
      const service = new ProjectsService(prisma as never, workspacesService as never);

      await service.create(OWNER_ID, {
        workspaceId: WORKSPACE_ID,
        name: "New App",
        sector: "Retail",
        productType: "Mobile",
        description: "A new project"
      });

      expect(workspacesService.ensureMember).toHaveBeenCalledWith(WORKSPACE_ID, OWNER_ID);
    });
  });
});
