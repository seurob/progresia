import { Injectable, NotFoundException } from "@nestjs/common";
import { ProjectsService } from "../projects/projects.service";
import { PrismaService } from "../../database/prisma.service";
import { CreateIdeaDto } from "./dto/create-idea.dto";

@Injectable()
export class IdeasService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly projectsService: ProjectsService
  ) {}

  async upsert(userId: string, dto: CreateIdeaDto) {
    const project = await this.projectsService.ensureProjectAccess(dto.projectId, userId);

    const data = {
      problem: dto.problem,
      targetUsers: dto.targetUsers,
      coreFeatures: dto.coreFeatures,
      complexity: dto.complexity ?? "standard",
      needsAi: dto.needsAi ?? false,
      needsAuth: dto.needsAuth ?? true,
      needsAdminPanel: dto.needsAdminPanel ?? true,
      constraints: dto.constraints,
      mainObjective: dto.mainObjective,
      techPreference: dto.techPreference,
      mandatoryTechs: dto.mandatoryTechs,
      architectureStyle: dto.architectureStyle,
      dataNeeds: dto.dataNeeds ?? [],
      aiNeeds: dto.aiNeeds,
      deploymentTarget: dto.deploymentTarget,
      expectedResults: dto.expectedResults ?? []
    };

    return this.prisma.idea.upsert({
      where: { projectId: project.id },
      create: { projectId: project.id, ...data },
      update: data
    });
  }

  async findByProject(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);

    const idea = await this.prisma.idea.findUnique({ where: { projectId: project.id } });

    if (!idea) {
      throw new NotFoundException("Idea not found");
    }

    return idea;
  }
}
