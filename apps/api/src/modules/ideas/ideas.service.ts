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
    await this.projectsService.ensureProjectAccess(dto.projectId, userId);

    return this.prisma.idea.upsert({
      where: { projectId: dto.projectId },
      create: {
        projectId: dto.projectId,
        problem: dto.problem,
        targetUsers: dto.targetUsers,
        coreFeatures: dto.coreFeatures,
        complexity: dto.complexity ?? "standard",
        needsAi: dto.needsAi ?? false,
        needsAuth: dto.needsAuth ?? true,
        needsAdminPanel: dto.needsAdminPanel ?? true,
        constraints: dto.constraints
      },
      update: {
        problem: dto.problem,
        targetUsers: dto.targetUsers,
        coreFeatures: dto.coreFeatures,
        complexity: dto.complexity ?? "standard",
        needsAi: dto.needsAi ?? false,
        needsAuth: dto.needsAuth ?? true,
        needsAdminPanel: dto.needsAdminPanel ?? true,
        constraints: dto.constraints
      }
    });
  }

  async findByProject(userId: string, projectId: string) {
    await this.projectsService.ensureProjectAccess(projectId, userId);

    const idea = await this.prisma.idea.findUnique({ where: { projectId } });

    if (!idea) {
      throw new NotFoundException("Idea not found");
    }

    return idea;
  }
}
