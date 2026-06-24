import { ConflictException, ForbiddenException, Injectable, NotFoundException } from "@nestjs/common";
import { Role } from "@prisma/client";
import { PrismaService } from "../../database/prisma.service";
import { CreateWorkspaceDto } from "./dto/create-workspace.dto";
import { InviteMemberDto } from "./dto/invite-member.dto";

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

  async listMembers(workspaceId: string, requesterId: string) {
    await this.ensureMember(workspaceId, requesterId);
    return this.prisma.workspaceMember.findMany({
      where: { workspaceId },
      include: {
        user: { select: { id: true, name: true, email: true } }
      },
      orderBy: { createdAt: "asc" }
    });
  }

  async inviteMember(workspaceId: string, inviterId: string, dto: InviteMemberDto) {
    const workspace = await this.ensureMember(workspaceId, inviterId);
    // ensureMember filters members by userId, so [0] is the requester's own membership record
    const requester = workspace.members[0];
    if (requester.role !== Role.OWNER) {
      throw new ForbiddenException("Only workspace owners can invite members");
    }

    const target = await this.prisma.user.findUnique({ where: { email: dto.email } });
    if (!target) {
      throw new NotFoundException("No user found with that email");
    }

    const existing = await this.prisma.workspaceMember.findUnique({
      where: { workspaceId_userId: { workspaceId, userId: target.id } }
    });
    if (existing) {
      throw new ConflictException("User is already a member of this workspace");
    }

    return this.prisma.workspaceMember.create({
      data: { workspaceId, userId: target.id, role: dto.role },
      include: {
        user: { select: { id: true, name: true, email: true } }
      }
    });
  }

  async removeMember(workspaceId: string, removerId: string, targetUserId: string) {
    const workspace = await this.ensureMember(workspaceId, removerId);
    const requester = workspace.members[0];
    if (requester.role !== Role.OWNER) {
      throw new ForbiddenException("Only workspace owners can remove members");
    }
    if (targetUserId === removerId) {
      throw new ForbiddenException("Cannot remove yourself from the workspace");
    }

    const target = await this.prisma.workspaceMember.findUnique({
      where: { workspaceId_userId: { workspaceId, userId: targetUserId } }
    });
    if (!target) {
      throw new NotFoundException("Member not found");
    }

    await this.prisma.workspaceMember.delete({
      where: { workspaceId_userId: { workspaceId, userId: targetUserId } }
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
