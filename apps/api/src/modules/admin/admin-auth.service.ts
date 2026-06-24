import { Injectable, UnauthorizedException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { JwtService } from "@nestjs/jwt";
import { Role } from "@prisma/client";
import * as bcrypt from "bcryptjs";
import { PrismaService } from "../../database/prisma.service";
import { toSafeUser } from "../../common/users/safe-user";
import { AdminLoginDto } from "./dto/admin-login.dto";

const ADMIN_TOKEN_TTL = "8h";
const GENERIC_ERROR = "Credenciales inválidas o permisos insuficientes";

@Injectable()
export class AdminAuthService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly jwtService: JwtService,
    private readonly config: ConfigService
  ) {}

  async login(dto: AdminLoginDto) {
    const user = await this.prisma.user.findFirst({
      where: {
        OR: [{ email: dto.identifier }, { name: dto.identifier }]
      }
    });

    if (!user || user.role !== Role.ADMIN) {
      throw new UnauthorizedException(GENERIC_ERROR);
    }

    const valid = await bcrypt.compare(dto.password, user.passwordHash);
    if (!valid) {
      throw new UnauthorizedException(GENERIC_ERROR);
    }

    const secret = this.config.get<string>("ADMIN_JWT_SECRET", "admin_change_me");
    const accessToken = this.jwtService.sign(
      { sub: user.id, email: user.email, role: user.role, type: "admin" },
      { secret, expiresIn: ADMIN_TOKEN_TTL }
    );

    return { accessToken, user: toSafeUser(user) };
  }

  async me(adminId: string) {
    const user = await this.prisma.user.findUniqueOrThrow({ where: { id: adminId } });
    return toSafeUser(user);
  }
}
