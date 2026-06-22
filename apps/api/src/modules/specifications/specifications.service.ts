import { ConflictException, Injectable } from "@nestjs/common";
import { Prisma, ProjectStatus, SpecificationStatus, SpecificationType } from "@prisma/client";
import { PrismaService } from "../../database/prisma.service";
import { AiServiceClient } from "../ai-service/ai-service.client";
import { ProjectsService } from "../projects/projects.service";
import { CreateSpecificationDto } from "./dto/create-specification.dto";

@Injectable()
export class SpecificationsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly projectsService: ProjectsService,
    private readonly aiServiceClient: AiServiceClient
  ) {}

  async create(userId: string, dto: CreateSpecificationDto) {
    await this.projectsService.ensureProjectAccess(dto.projectId, userId);

    return this.prisma.specification.create({
      data: {
        projectId: dto.projectId,
        type: dto.type,
        status: dto.status,
        content: dto.content as Prisma.InputJsonValue
      }
    });
  }

  async listByProject(userId: string, projectId: string) {
    await this.projectsService.ensureProjectAccess(projectId, userId);

    return this.prisma.specification.findMany({
      where: { projectId },
      orderBy: { createdAt: "desc" }
    });
  }

  async generateRequirements(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const idea = await this.prisma.idea.findUnique({ where: { projectId } });

    if (!idea) {
      throw new ConflictException("Idea intake is required before generating requirements");
    }

    const aiPayload = {
      name: project.name,
      sector: project.sector,
      problem: idea.problem,
      target_users: idea.targetUsers,
      core_features: idea.coreFeatures,
      needs_auth: idea.needsAuth,
      needs_admin_panel: idea.needsAdminPanel,
      needs_ai: idea.needsAi
    };

    const generated = await this.aiServiceClient.generateRequirements(aiPayload);

    const [specification] = await this.prisma.$transaction([
      this.prisma.specification.create({
        data: {
          projectId,
          type: SpecificationType.REQUIREMENTS,
          status: SpecificationStatus.GENERATED,
          content: generated as unknown as Prisma.InputJsonValue
        }
      }),
      this.prisma.project.update({
        where: { id: projectId },
        data: { status: ProjectStatus.REQUIREMENTS_READY }
      })
    ]);

    return specification;
  }

  async generateOpenSpec(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const idea = await this.prisma.idea.findUnique({ where: { projectId } });

    if (!idea) {
      throw new ConflictException("Idea intake is required before generating OpenSpec");
    }

    // If an architecture recommendation was already generated, embed it in the OpenSpec
    // so the specification document reflects the chosen technology stack.
    const archSpec = await this.prisma.specification.findFirst({
      where: { projectId, type: SpecificationType.ARCHITECTURE, status: SpecificationStatus.GENERATED },
      orderBy: { createdAt: "desc" }
    });
    const architectureType = (archSpec?.content as Record<string, unknown>)?.architecture_type as string | undefined;

    const generated = await this.aiServiceClient.generateOpenSpec({
      name: project.name,
      sector: project.sector,
      problem: idea.problem,
      target_users: idea.targetUsers,
      core_features: idea.coreFeatures,
      needs_auth: idea.needsAuth,
      needs_admin_panel: idea.needsAdminPanel,
      needs_ai: idea.needsAi,
      architecture_type: architectureType
    });

    // Atomic: create spec + advance project to SPEC_READY
    const [specification] = await this.prisma.$transaction([
      this.prisma.specification.create({
        data: {
          projectId,
          type: SpecificationType.OPENSPEC,
          status: SpecificationStatus.GENERATED,
          content: {
            ...generated.spec,
            generatedBy: "ai-service",
            projectName: generated.project_name
          } as Prisma.InputJsonValue
        }
      }),
      this.prisma.project.update({
        where: { id: projectId },
        data: { status: ProjectStatus.SPEC_READY }
      })
    ]);

    return specification;
  }

  async generateIssues(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);

    const openspecSpec = await this.prisma.specification.findFirst({
      where: { projectId, type: SpecificationType.OPENSPEC, status: SpecificationStatus.GENERATED },
      orderBy: { createdAt: "desc" }
    });

    if (!openspecSpec) {
      throw new ConflictException("Generated OpenSpec is required before generating GitHub Issues");
    }

    const result = await this.aiServiceClient.generateIssues({
      project_name: project.name,
      sector:       project.sector,
      openspec:     openspecSpec.content as Record<string, unknown>
    });

    return this.prisma.specification.create({
      data: {
        projectId,
        type:    SpecificationType.ISSUES,
        status:  SpecificationStatus.GENERATED,
        content: result as unknown as Prisma.InputJsonValue
      }
    });
  }

  async generateTutorial(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const idea    = await this.prisma.idea.findUnique({ where: { projectId } });

    const openspecSpec = await this.prisma.specification.findFirst({
      where: { projectId, type: SpecificationType.OPENSPEC, status: SpecificationStatus.GENERATED },
      orderBy: { createdAt: "desc" }
    });

    if (!openspecSpec) {
      throw new ConflictException("Generated OpenSpec is required before generating a tutorial");
    }

    const spec = openspecSpec.content as Record<string, unknown>;
    const archSection = (typeof spec.architecture === "object" && spec.architecture)
      ? (spec.architecture as Record<string, unknown>)
      : {};

    const modules      = Array.isArray(spec.modules)      ? (spec.modules      as string[])                                                        : [];
    const requirements = Array.isArray(spec.requirements) ? (spec.requirements as Array<{ id: string; title: string; description: string }>)        : [];
    const stack        = Array.isArray(archSection.stack)  ? (archSection.stack  as string[])                                                        : [];
    const archType     = (archSection.type as string | undefined) ?? "";

    const tutorial = await this.aiServiceClient.generateTutorial({
      project_name:     project.name,
      sector:           project.sector,
      architecture_type: archType,
      stack,
      modules,
      requirements,
      needs_auth:       idea?.needsAuth       ?? true,
      needs_admin_panel: idea?.needsAdminPanel ?? true,
    });

    return this.prisma.specification.create({
      data: {
        projectId,
        type:    SpecificationType.TUTORIAL,
        status:  SpecificationStatus.GENERATED,
        content: tutorial as unknown as Prisma.InputJsonValue
      }
    });
  }

  async generateArchitecture(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const idea = await this.prisma.idea.findUnique({ where: { projectId } });

    if (!idea) {
      throw new ConflictException("Idea intake is required before generating architecture recommendation");
    }

    const recommendation = await this.aiServiceClient.recommendArchitecture({
      project_name:   project.name,
      sector:         project.sector,
      problem:        idea.problem,
      target_users:   idea.targetUsers,
      key_features:   idea.coreFeatures,
      needs_auth:     idea.needsAuth,
      needs_admin_panel: idea.needsAdminPanel,
      needs_ai:       idea.needsAi,
      preferred_stack: ""
    });

    return this.prisma.specification.create({
      data: {
        projectId,
        type:    SpecificationType.ARCHITECTURE,
        status:  SpecificationStatus.GENERATED,
        content: recommendation as unknown as Prisma.InputJsonValue
      }
    });
  }
}
