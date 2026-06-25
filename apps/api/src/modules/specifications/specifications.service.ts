import { ConflictException, Injectable, NotFoundException } from "@nestjs/common";
import { Prisma, ProjectStatus, SpecificationStatus, SpecificationType } from "@prisma/client";
import { PrismaService } from "../../database/prisma.service";
import { AiServiceClient } from "../ai-service/ai-service.client";
import { ProjectsService } from "../projects/projects.service";
import { complexityToLevel } from "../../common/utils/project";
import { CreateSpecificationDto } from "./dto/create-specification.dto";
import { SpecificationExportService } from "./specifications.export.service";

@Injectable()
export class SpecificationsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly projectsService: ProjectsService,
    private readonly aiServiceClient: AiServiceClient,
    private readonly exportService: SpecificationExportService
  ) {}

  async create(userId: string, dto: CreateSpecificationDto) {
    const project = await this.projectsService.ensureProjectAccess(dto.projectId, userId);

    return this.prisma.specification.create({
      data: {
        projectId: project.id,
        type: dto.type,
        status: dto.status,
        content: dto.content as Prisma.InputJsonValue
      }
    });
  }

  async listByProject(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);

    return this.prisma.specification.findMany({
      where: { projectId: project.id },
      orderBy: { createdAt: "desc" }
    });
  }

  async exportPdf(userId: string, specificationId: string): Promise<{ filename: string; buffer: Buffer }> {
    const specification = await this.prisma.specification.findUnique({
      where: { id: specificationId },
      include: { project: true }
    });

    if (!specification) throw new NotFoundException("Specification not found");
    await this.projectsService.ensureProjectAccess(specification.projectId, userId);

    const input = {
      projectName: specification.project.name,
      type: specification.type,
      createdAt: specification.createdAt,
      content: specification.content as Record<string, unknown>
    };

    return {
      filename: this.exportService.buildFilename(specification.project.name, specification.type, "pdf"),
      buffer: this.exportService.toPdf(input)
    };
  }

  async exportMd(userId: string, specificationId: string): Promise<{ filename: string; content: string }> {
    const specification = await this.prisma.specification.findUnique({
      where: { id: specificationId },
      include: { project: true }
    });

    if (!specification) throw new NotFoundException("Specification not found");
    await this.projectsService.ensureProjectAccess(specification.projectId, userId);

    const input = {
      projectName: specification.project.name,
      type: specification.type,
      createdAt: specification.createdAt,
      content: specification.content as Record<string, unknown>
    };

    return {
      filename: this.exportService.buildFilename(specification.project.name, specification.type, "md"),
      content: this.exportService.toMarkdown(input)
    };
  }

  async generateRequirements(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const id = project.id;
    const idea = await this.prisma.idea.findUnique({ where: { projectId: id } });

    if (!idea) {
      throw new ConflictException("Idea intake is required before generating requirements");
    }

    const generated = await this.aiServiceClient.generateRequirements({
      name: project.name,
      sector: project.sector,
      problem: idea.problem,
      target_users: idea.targetUsers,
      core_features: idea.coreFeatures,
      needs_auth: idea.needsAuth,
      needs_admin_panel: idea.needsAdminPanel,
      needs_ai: idea.needsAi,
      technical_level: complexityToLevel(idea.complexity),
      product_type: project.productType ?? "web"
    });

    const [specification] = await this.prisma.$transaction([
      this.prisma.specification.create({
        data: {
          projectId: id,
          type: SpecificationType.REQUIREMENTS,
          status: SpecificationStatus.GENERATED,
          content: generated as unknown as Prisma.InputJsonValue
        }
      }),
      this.prisma.project.update({
        where: { id },
        data: { status: ProjectStatus.REQUIREMENTS_READY }
      })
    ]);

    return specification;
  }

  async generateOpenSpec(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const id = project.id;
    const idea = await this.prisma.idea.findUnique({ where: { projectId: id } });

    if (!idea) {
      throw new ConflictException("Idea intake is required before generating OpenSpec");
    }

    const archSpec = await this.prisma.specification.findFirst({
      where: { projectId: id, type: SpecificationType.ARCHITECTURE, status: SpecificationStatus.GENERATED },
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
      technical_level: complexityToLevel(idea.complexity),
      architecture_type: architectureType,
      product_type: project.productType ?? "web"
    });

    const [specification] = await this.prisma.$transaction([
      this.prisma.specification.create({
        data: {
          projectId: id,
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
        where: { id },
        data: { status: ProjectStatus.SPEC_READY }
      })
    ]);

    return specification;
  }

  async proposeTech(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const id = project.id;
    const idea = await this.prisma.idea.findUnique({ where: { projectId: id } });

    if (!idea) {
      throw new ConflictException("Idea intake is required before generating tech proposals");
    }

    const level = complexityToLevel(idea.complexity);

    // product_type overrides architecture_style for unambiguous cases (mobile/desktop),
    // so the catalog always picks the right stack even if the wizard fell back to a web arch.
    const productTypeArchMap: Record<string, string> = {
      mobile:  "mobile_api",
      desktop: "desktop_api",
    };
    const architectureStyle =
      productTypeArchMap[project.productType ?? ""] ?? idea.architectureStyle ?? "frontend_api";

    const proposals = await this.aiServiceClient.proposeTech({
      name: project.name,
      sector: project.sector,
      level,
      product_type: project.productType ?? "web",
      main_objective: idea.mainObjective ?? "mvp",
      architecture_style: architectureStyle,
      data_needs: idea.dataNeeds ?? [],
      ai_needs: idea.aiNeeds ?? "none",
      deployment_target: idea.deploymentTarget ?? "docker_local",
      core_features: idea.coreFeatures,
      mandatory_techs: idea.mandatoryTechs ?? undefined
    });

    await this.prisma.specification.create({
      data: {
        projectId: id,
        type: SpecificationType.TECH_PROPOSAL,
        status: SpecificationStatus.GENERATED,
        content: proposals as unknown as Prisma.InputJsonValue
      }
    });

    return proposals;
  }

  async generateIssues(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const id = project.id;

    const openspecSpec = await this.prisma.specification.findFirst({
      where: { projectId: id, type: SpecificationType.OPENSPEC, status: SpecificationStatus.GENERATED },
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
        projectId: id,
        type:    SpecificationType.ISSUES,
        status:  SpecificationStatus.GENERATED,
        content: result as unknown as Prisma.InputJsonValue
      }
    });
  }

  async generateTutorial(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const id = project.id;
    const idea = await this.prisma.idea.findUnique({ where: { projectId: id } });

    const openspecSpec = await this.prisma.specification.findFirst({
      where: { projectId: id, type: SpecificationType.OPENSPEC, status: SpecificationStatus.GENERATED },
      orderBy: { createdAt: "desc" }
    });

    if (!openspecSpec) {
      throw new ConflictException("Generated OpenSpec is required before generating a tutorial");
    }

    const spec = openspecSpec.content as Record<string, unknown>;
    const archSection = (typeof spec.architecture === "object" && spec.architecture)
      ? (spec.architecture as Record<string, unknown>)
      : {};

    const modules      = Array.isArray(spec.modules)      ? (spec.modules      as string[])                                                  : [];
    const requirements = Array.isArray(spec.requirements) ? (spec.requirements as Array<{ id: string; title: string; description: string }>) : [];
    const stack        = Array.isArray(archSection.stack)  ? (archSection.stack  as string[])                                                  : [];
    const archType     = (archSection.type as string | undefined) ?? "";

    const tutorial = await this.aiServiceClient.generateTutorial({
      project_name:      project.name,
      sector:            project.sector,
      architecture_type: archType,
      stack,
      modules,
      requirements,
      needs_auth:        idea?.needsAuth       ?? true,
      needs_admin_panel: idea?.needsAdminPanel ?? true,
    });

    return this.prisma.specification.create({
      data: {
        projectId: id,
        type:    SpecificationType.TUTORIAL,
        status:  SpecificationStatus.GENERATED,
        content: tutorial as unknown as Prisma.InputJsonValue
      }
    });
  }

  async generateArchitecture(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const id = project.id;
    const idea = await this.prisma.idea.findUnique({ where: { projectId: id } });

    if (!idea) {
      throw new ConflictException("Idea intake is required before generating architecture recommendation");
    }

    const recommendation = await this.aiServiceClient.recommendArchitecture({
      project_name:      project.name,
      sector:            project.sector,
      problem:           idea.problem,
      target_users:      idea.targetUsers,
      key_features:      idea.coreFeatures,
      needs_auth:        idea.needsAuth,
      needs_admin_panel: idea.needsAdminPanel,
      needs_ai:          idea.needsAi,
      preferred_stack:   "",
      technical_level:   complexityToLevel(idea.complexity),
      product_type:      project.productType ?? "web"
    });

    return this.prisma.specification.create({
      data: {
        projectId: id,
        type:    SpecificationType.ARCHITECTURE,
        status:  SpecificationStatus.GENERATED,
        content: recommendation as unknown as Prisma.InputJsonValue
      }
    });
  }
}
