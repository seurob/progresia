import { BadRequestException, ConflictException, Injectable, NotFoundException } from "@nestjs/common";
import { Role } from "@prisma/client";
import * as bcrypt from "bcryptjs";
import { PrismaService } from "../../database/prisma.service";
import { toSafeUser } from "../../common/users/safe-user";
import { AdminCreateUserDto } from "./dto/admin-create-user.dto";
import { AdminUpdateUserDto } from "./dto/admin-update-user.dto";

@Injectable()
export class AdminUsersService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(search?: string) {
    const users = await this.prisma.user.findMany({
      where: search
        ? {
            OR: [
              { name: { contains: search, mode: "insensitive" } },
              { email: { contains: search, mode: "insensitive" } }
            ]
          }
        : undefined,
      orderBy: { createdAt: "asc" }
    });
    return users.map(toSafeUser);
  }

  async create(dto: AdminCreateUserDto) {
    const exists = await this.prisma.user.findUnique({ where: { email: dto.email } });
    if (exists) throw new ConflictException("Email ya registrado");

    const passwordHash = await bcrypt.hash(dto.password, 12);

    const user = await this.prisma.$transaction(async (tx) => {
      const created = await tx.user.create({
        data: {
          email: dto.email,
          name: dto.name,
          passwordHash,
          role: dto.role ?? Role.OWNER
        }
      });

      await tx.workspace.create({
        data: {
          name: `${dto.name}'s Workspace`,
          ownerId: created.id,
          members: { create: { userId: created.id, role: Role.OWNER } }
        }
      });

      return created;
    });

    return toSafeUser(user);
  }

  async update(id: string, dto: AdminUpdateUserDto, adminId: string) {
    const user = await this.prisma.user.findUnique({ where: { id } });
    if (!user) throw new NotFoundException("Usuario no encontrado");

    if (id === adminId && dto.role && dto.role !== Role.ADMIN) {
      throw new BadRequestException("No puedes retirar tu propio rol de administrador");
    }

    if (dto.role && dto.role !== Role.ADMIN && user.role === Role.ADMIN) {
      const adminCount = await this.prisma.user.count({ where: { role: Role.ADMIN } });
      if (adminCount <= 1) {
        throw new BadRequestException("No se puede retirar el rol al último administrador");
      }
    }

    if (dto.email && dto.email !== user.email) {
      const exists = await this.prisma.user.findUnique({ where: { email: dto.email } });
      if (exists) throw new ConflictException("Email ya registrado");
    }

    const data: Record<string, unknown> = {};
    if (dto.name !== undefined) data.name = dto.name;
    if (dto.email !== undefined) data.email = dto.email;
    if (dto.role !== undefined) data.role = dto.role;
    if (dto.password) data.passwordHash = await bcrypt.hash(dto.password, 12);

    const updated = await this.prisma.user.update({ where: { id }, data });
    return toSafeUser(updated);
  }

  async remove(id: string, adminId: string) {
    if (id === adminId) {
      throw new BadRequestException("No puedes eliminar tu propia cuenta");
    }

    const user = await this.prisma.user.findUnique({ where: { id } });
    if (!user) throw new NotFoundException("Usuario no encontrado");

    if (user.role === Role.ADMIN) {
      const adminCount = await this.prisma.user.count({ where: { role: Role.ADMIN } });
      if (adminCount <= 1) {
        throw new BadRequestException("No se puede eliminar el último administrador");
      }
    }

    await this.prisma.user.delete({ where: { id } });
  }
}
