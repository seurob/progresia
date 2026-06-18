import { Injectable } from "@nestjs/common";
import { Prisma } from "@prisma/client";
import { PrismaService } from "../../database/prisma.service";
import { ProjectsService } from "../projects/projects.service";
import { CreateSpecificationDto } from "./dto/create-specification.dto";

@Injectable()
export class SpecificationsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly projectsService: ProjectsService
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
}
