import { ConflictException } from "@nestjs/common";
import { SpecificationStatus, SpecificationType } from "@prisma/client";
import { ArtifactsService } from "./artifacts.service";

describe("ArtifactsService", () => {
  const project = {
    id: "project-1",
    name: "Reservas Clinica"
  };

  const aiServiceClientMock = {} as never;
  const githubServiceMock = {} as never;
  const storageServiceMock = {} as never;

  it("generates and persists an artifact bundle manifest from latest OpenSpec", async () => {
    const specification = {
      id: "spec-1",
      content: { project: { name: "Reservas Clinica" }, requirements: ["Login"] }
    };
    const prisma = {
      specification: {
        findFirst: jest.fn().mockResolvedValue(specification)
      },
      artifactBundle: {
        // findFirst returns null — no prior bundle, so create is called
        findFirst: jest.fn().mockResolvedValue(null),
        create: jest.fn().mockResolvedValue({ id: "bundle-1" })
      }
    };
    const projectsService = {
      ensureProjectAccess: jest.fn().mockResolvedValue(project)
    };
    const service = new ArtifactsService(
      prisma as never,
      projectsService as never,
      aiServiceClientMock,
      githubServiceMock,
      storageServiceMock
    );

    await expect(service.generateBundle("user-1", "project-1")).resolves.toEqual({ id: "bundle-1" });

    expect(prisma.specification.findFirst).toHaveBeenCalledWith({
      where: {
        projectId: "project-1",
        type: SpecificationType.OPENSPEC,
        status: SpecificationStatus.GENERATED
      },
      orderBy: { createdAt: "desc" }
    });
    expect(prisma.artifactBundle.create).toHaveBeenCalledWith({
      data: expect.objectContaining({
        projectId: "project-1",
        specificationId: "spec-1",
        manifest: expect.objectContaining({
          project: "Reservas Clinica",
          sourceSpecificationId: "spec-1",
          files: expect.arrayContaining([
            expect.objectContaining({ path: "reservas-clinica/README.md" }),
            expect.objectContaining({ path: "reservas-clinica/sdd/requirements/requirements.md" }),
            expect.objectContaining({ path: "reservas-clinica/sdd/constitution.md" }),
            expect.objectContaining({ path: "reservas-clinica/sdd/specifications/openspec.json" })
          ])
        })
      })
    });
  });

  it("rejects bundle generation when no generated OpenSpec exists", async () => {
    const prisma = {
      specification: {
        findFirst: jest.fn().mockResolvedValue(null)
      }
    };
    const projectsService = {
      ensureProjectAccess: jest.fn().mockResolvedValue(project)
    };
    const service = new ArtifactsService(
      prisma as never,
      projectsService as never,
      aiServiceClientMock,
      githubServiceMock,
      storageServiceMock
    );

    await expect(service.generateBundle("user-1", "project-1")).rejects.toBeInstanceOf(
      ConflictException
    );
  });
});
