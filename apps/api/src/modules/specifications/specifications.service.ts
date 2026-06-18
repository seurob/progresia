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

    return this.prisma.specification.create({
      data: {
        projectId,
        type: SpecificationType.REQUIREMENTS,
        status: SpecificationStatus.GENERATED,
        content: generated as unknown as Prisma.InputJsonValue
      }
    });
  }

  async generateOpenSpec(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const idea = await this.prisma.idea.findUnique({ where: { projectId } });

    if (!idea) {
      throw new ConflictException("Idea intake is required before generating OpenSpec");
    }

    const generated = await this.aiServiceClient.generateOpenSpec({
      name: project.name,
      sector: project.sector,
      problem: idea.problem,
      target_users: idea.targetUsers,
      core_features: idea.coreFeatures,
      needs_auth: idea.needsAuth,
      needs_admin_panel: idea.needsAdminPanel,
      needs_ai: idea.needsAi
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
}
