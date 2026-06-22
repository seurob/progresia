import { Injectable, NotFoundException } from "@nestjs/common";
import { PrismaService } from "../../database/prisma.service";
import { toSafeUser } from "../../common/users/safe-user";

@Injectable()
export class UsersService {
  constructor(private readonly prisma: PrismaService) {}

  async findMe(userId: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });

    if (!user) {
      throw new NotFoundException("User not found");
    }

    return toSafeUser(user);
  }

  async findAll() {
    const users = await this.prisma.user.findMany({ orderBy: { createdAt: "asc" } });
    return users.map(toSafeUser);
  }
}
