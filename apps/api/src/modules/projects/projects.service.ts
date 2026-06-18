import { ForbiddenException, Injectable, NotFoundException } from "@nestjs/common";
import { PrismaService } from "../../database/prisma.service";
import { WorkspacesService } from "../workspaces/workspaces.service";
import { CreateProjectDto } from "./dto/create-project.dto";
import { UpdateProjectDto } from "./dto/update-project.dto";

@Injectable()
export class ProjectsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly workspacesService: WorkspacesService
  ) {}

  async create(userId: string, dto: CreateProjectDto) {
    await this.workspacesService.ensureMember(dto.workspaceId, userId);

    return this.prisma.project.create({
      data: {
        workspaceId: dto.workspaceId,
        name: dto.name,
        sector: dto.sector,
        productType: dto.productType,
        description: dto.description
      }
    });
  }

  async listForUser(userId: string) {
    return this.prisma.project.findMany({
      where: {
        workspace: {
          members: {
            some: { userId }
          }
        }
      },
      include: {
        idea: true,
        specifications: true
      },
      orderBy: { createdAt: "desc" }
    });
  }

  async findOne(userId: string, projectId: string) {
    await this.ensureProjectAccess(projectId, userId);

    return this.prisma.project.findUnique({
      where: { id: projectId },
      include: {
        idea: true,
        specifications: true
      }
    });
  }

  async update(userId: string, projectId: string, dto: UpdateProjectDto) {
    await this.ensureProjectAccess(projectId, userId);

    return this.prisma.project.update({
      where: { id: projectId },
      data: {
        name: dto.name,
        sector: dto.sector,
        productType: dto.productType,
        description: dto.description
      }
    });
  }

  async ensureProjectAccess(projectId: string, userId: string) {
    const project = await this.prisma.project.findUnique({
      where: { id: projectId },
      include: {
        workspace: {
          include: {
            members: {
              where: { userId }
            }
          }
        }
      }
    });

    if (!project) {
      throw new NotFoundException("Project not found");
    }

    if (project.workspace.members.length === 0) {
      throw new ForbiddenException("Project access denied");
    }

    return project;
  }
}
