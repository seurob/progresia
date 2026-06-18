import { ConflictException } from "@nestjs/common";
import { ProjectStatus, SpecificationStatus, SpecificationType } from "@prisma/client";
import { SpecificationsService } from "./specifications.service";

describe("SpecificationsService", () => {
  const project = {
    id: "project-1",
    name: "Reservas",
    sector: "Educacion"
  };
  const idea = {
    problem: "Gestionar reservas manuales consume demasiado tiempo",
    targetUsers: "Profesores",
    coreFeatures: ["CRUD profesores", "Reservas"],
    needsAuth: true,
    needsAdminPanel: true,
    needsAi: false
  };

  it("generates and persists OpenSpec from AI service", async () => {
    const prisma = {
      idea: {
        findUnique: jest.fn().mockResolvedValue(idea)
      },
      specification: {
        create: jest.fn().mockResolvedValue({ id: "spec-1" })
      },
      project: {
        update: jest.fn().mockResolvedValue({ id: "project-1", status: ProjectStatus.SPEC_READY })
      },
      $transaction: jest.fn((operations: Array<Promise<unknown>>) => Promise.all(operations))
    };
    const projectsService = {
      ensureProjectAccess: jest.fn().mockResolvedValue(project)
    };
    const aiServiceClient = {
      generateOpenSpec: jest.fn().mockResolvedValue({
        project_name: "Reservas",
        spec: { project: { name: "Reservas" } }
      })
    };
    const service = new SpecificationsService(
      prisma as never,
      projectsService as never,
      aiServiceClient as never
    );

    await expect(service.generateOpenSpec("user-1", "project-1")).resolves.toEqual({ id: "spec-1" });

    expect(aiServiceClient.generateOpenSpec).toHaveBeenCalledWith({
      name: "Reservas",
      sector: "Educacion",
      problem: idea.problem,
      target_users: idea.targetUsers,
      core_features: idea.coreFeatures,
      needs_auth: true,
      needs_admin_panel: true,
      needs_ai: false
    });
    expect(prisma.specification.create).toHaveBeenCalledWith({
      data: {
        projectId: "project-1",
        type: SpecificationType.OPENSPEC,
        status: SpecificationStatus.GENERATED,
        content: {
          project: { name: "Reservas" },
          generatedBy: "ai-service",
          projectName: "Reservas"
        }
      }
    });
    expect(prisma.project.update).toHaveBeenCalledWith({
      where: { id: "project-1" },
      data: { status: ProjectStatus.SPEC_READY }
    });
  });

  it("rejects generation when project has no idea intake", async () => {
    const prisma = {
      idea: {
        findUnique: jest.fn().mockResolvedValue(null)
      }
    };
    const projectsService = {
      ensureProjectAccess: jest.fn().mockResolvedValue(project)
    };
    const service = new SpecificationsService(
      prisma as never,
      projectsService as never,
      {} as never
    );

    await expect(service.generateOpenSpec("user-1", "project-1")).rejects.toBeInstanceOf(
      ConflictException
    );
  });
});
