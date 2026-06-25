import { ConflictException } from "@nestjs/common";
import { ProjectStatus, SpecificationStatus, SpecificationType } from "@prisma/client";
import { SpecificationExportService } from "./specifications.export.service";
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
        // findFirst returns null — no prior architecture spec in this scenario
        findFirst: jest.fn().mockResolvedValue(null),
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
      aiServiceClient as never,
      new SpecificationExportService()
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
      needs_ai: false,
      technical_level: "INTERMEDIATE", // complexityToLevel(undefined) → INTERMEDIATE
      architecture_type: undefined,     // no architecture spec in this test scenario
      product_type: "web"               // project.productType ?? "web" (not set in mock → default)
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
      {} as never,
      new SpecificationExportService()
    );

    await expect(service.generateOpenSpec("user-1", "project-1")).rejects.toBeInstanceOf(
      ConflictException
    );
  });

  it("exports a generated specification as PDF", async () => {
    const prisma = {
      specification: {
        findUnique: jest.fn().mockResolvedValue({
          id: "spec-1",
          projectId: "project-1",
          type: SpecificationType.OPENSPEC,
          createdAt: new Date("2026-06-23T00:00:00.000Z"),
          project,
          content: {
            project: { description: "Sistema de reservas para profesores" },
            architecture: { stack: ["React", "NestJS", "PostgreSQL"] },
            modules: ["Reservas"],
            requirements: [{ id: "RF-001", title: "Crear reserva", description: "Permite crear reservas" }],
            user_stories: [{ actor: "profesor", goal: "reservar aula", benefit: "organizar clase" }]
          }
        })
      }
    };
    const projectsService = {
      ensureProjectAccess: jest.fn().mockResolvedValue(project)
    };
    const service = new SpecificationsService(
      prisma as never,
      projectsService as never,
      {} as never,
      new SpecificationExportService()
    );

    const result = await service.exportPdf("user-1", "spec-1");

    expect(result.filename).toBe("reservas-openspec.pdf");
    expect(result.buffer.subarray(0, 8).toString("latin1")).toBe("%PDF-1.4");
    expect(projectsService.ensureProjectAccess).toHaveBeenCalledWith("project-1", "user-1");
  });
});
