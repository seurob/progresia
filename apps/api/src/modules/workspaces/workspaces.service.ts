import { ForbiddenException, Injectable, NotFoundException } from "@nestjs/common";
import { Role } from "@prisma/client";
import { PrismaService } from "../../database/prisma.service";
import { CreateWorkspaceDto } from "./dto/create-workspace.dto";

@Injectable()
export class WorkspacesService {
  constructor(private readonly prisma: PrismaService) {}

  async create(userId: string, dto: CreateWorkspaceDto) {
    return this.prisma.workspace.create({
      data: {
        name: dto.name,
        ownerId: userId,
        members: {
          create: {
            userId,
            role: Role.OWNER
          }
        }
      },
      include: {
        members: true
      }
    });
  }

  async listForUser(userId: string) {
    return this.prisma.workspace.findMany({
      where: {
        members: {
          some: { userId }
        }
      },
      orderBy: { createdAt: "desc" }
    });
  }

  async ensureMember(workspaceId: string, userId: string) {
    const workspace = await this.prisma.workspace.findUnique({
      where: { id: workspaceId },
      include: {
        members: {
          where: { userId }
        }
      }
    });

    if (!workspace) {
      throw new NotFoundException("Workspace not found");
    }

    if (workspace.members.length === 0) {
      throw new ForbiddenException("Workspace access denied");
    }

    return workspace;
  }
}
