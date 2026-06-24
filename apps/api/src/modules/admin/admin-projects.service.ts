import { BadRequestException, Injectable, NotFoundException } from "@nestjs/common";
import { PrismaService } from "../../database/prisma.service";
import { slugify } from "../../common/utils/string";
import { AdminCreateProjectDto } from "./dto/admin-create-project.dto";
import { AdminUpdateProjectDto } from "./dto/admin-update-project.dto";

const OWNER_SELECT = { select: { id: true, name: true, email: true } };

@Injectable()
export class AdminProjectsService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(search?: string) {
    return this.prisma.project.findMany({
      where: search ? { name: { contains: search, mode: "insensitive" } } : undefined,
      include: {
        workspace: { include: { owner: OWNER_SELECT } }
      },
      orderBy: { createdAt: "desc" }
    });
  }

  async create(dto: AdminCreateProjectDto) {
    const owner = await this.prisma.user.findUnique({ where: { id: dto.ownerId } });
    if (!owner) throw new NotFoundException("Propietario no encontrado");

    const workspace = await this.prisma.workspace.findFirst({ where: { ownerId: dto.ownerId } });
    if (!workspace) throw new BadRequestException("El propietario no tiene workspace");

    const slug = await this.generateSlug(dto.name);

    return this.prisma.project.create({
      data: {
        workspaceId: workspace.id,
        name: dto.name,
        slug,
        sector: dto.sector,
        productType: dto.productType,
        description: dto.description
      },
      include: { workspace: { include: { owner: OWNER_SELECT } } }
    });
  }

  async update(id: string, dto: AdminUpdateProjectDto) {
    const project = await this.prisma.project.findUnique({ where: { id } });
    if (!project) throw new NotFoundException("Proyecto no encontrado");

    const data: Record<string, unknown> = {};
    if (dto.name !== undefined) {
      data.name = dto.name;
      data.slug = await this.generateSlug(dto.name, id);
    }
    if (dto.sector !== undefined) data.sector = dto.sector;
    if (dto.productType !== undefined) data.productType = dto.productType;
    if (dto.description !== undefined) data.description = dto.description;
    if (dto.status !== undefined) data.status = dto.status;

    return this.prisma.project.update({
      where: { id },
      data,
      include: { workspace: { include: { owner: OWNER_SELECT } } }
    });
  }

  async remove(id: string) {
    const project = await this.prisma.project.findUnique({ where: { id } });
    if (!project) throw new NotFoundException("Proyecto no encontrado");
    await this.prisma.project.delete({ where: { id } });
  }

  private async generateSlug(name: string, excludeId?: string): Promise<string> {
    const base = slugify(name);
    let slug = base;
    for (let i = 1; i <= 99; i++) {
      const exists = await this.prisma.project.findUnique({
        where: { slug },
        select: { id: true }
      });
      if (!exists || exists.id === excludeId) return slug;
      slug = `${base}-${i}`;
    }
    return `${base}-${Date.now()}`;
  }
}
