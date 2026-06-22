import { ForbiddenException, Injectable, NotFoundException } from "@nestjs/common";
import { PrismaService } from "../../database/prisma.service";
import { WorkspacesService } from "../workspaces/workspaces.service";
import { CreateProjectDto } from "./dto/create-project.dto";
import { UpdateProjectDto } from "./dto/update-project.dto";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function slugify(text: string): string {
  return (
    text
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "")
      .substring(0, 50) || "proyecto"
  );
}

@Injectable()
export class ProjectsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly workspacesService: WorkspacesService
  ) {}

  private async generateUniqueSlug(name: string): Promise<string> {
    const base = slugify(name);
    let slug = base;
    let counter = 1;
    while (await this.prisma.project.findUnique({ where: { slug } })) {
      slug = `${base}-${counter++}`;
    }
    return slug;
  }

  async create(userId: string, dto: CreateProjectDto) {
    await this.workspacesService.ensureMember(dto.workspaceId, userId);
    const slug = await this.generateUniqueSlug(dto.name);

    return this.prisma.project.create({
      data: {
        workspaceId: dto.workspaceId,
        name: dto.name,
        slug,
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
        specifications: true,
        artifactBundles: true
      },
      orderBy: { createdAt: "desc" }
    });
  }

  async findOne(userId: string, projectIdOrSlug: string) {
    await this.ensureProjectAccess(projectIdOrSlug, userId);

    const where = UUID_RE.test(projectIdOrSlug)
      ? { id: projectIdOrSlug }
      : { slug: projectIdOrSlug };

    return this.prisma.project.findUnique({
      where,
      include: {
        idea: true,
        specifications: true,
        artifactBundles: true
      }
    });
  }

  async update(userId: string, projectIdOrSlug: string, dto: UpdateProjectDto) {
    const project = await this.ensureProjectAccess(projectIdOrSlug, userId);

    return this.prisma.project.update({
      where: { id: project.id },
      data: {
        name: dto.name,
        sector: dto.sector,
        productType: dto.productType,
        description: dto.description
      }
    });
  }

  async remove(userId: string, projectIdOrSlug: string) {
    const project = await this.ensureProjectAccess(projectIdOrSlug, userId);
    await this.prisma.project.delete({ where: { id: project.id } });
  }

  async ensureProjectAccess(projectIdOrSlug: string, userId: string) {
    const where = UUID_RE.test(projectIdOrSlug)
      ? { id: projectIdOrSlug }
      : { slug: projectIdOrSlug };

    const project = await this.prisma.project.findUnique({
      where,
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
