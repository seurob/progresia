import { ConflictException, Injectable, UnauthorizedException } from "@nestjs/common";
import { JwtService } from "@nestjs/jwt";
import { ConfigService } from "@nestjs/config";
import { Role, User } from "@prisma/client";
import * as bcrypt from "bcryptjs";
import { createHash, randomBytes } from "node:crypto";
import { PrismaService } from "../../database/prisma.service";
import { toSafeUser } from "../../common/users/safe-user";
import { LoginDto } from "./dto/login.dto";
import { RegisterDto } from "./dto/register.dto";

const REFRESH_TOKEN_TTL_DAYS = 7;
const REFRESH_TOKEN_BYTES = 48;

function hashToken(raw: string): string {
  return createHash("sha256").update(raw).digest("hex");
}

@Injectable()
export class AuthService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly jwtService: JwtService,
    private readonly config: ConfigService
  ) {}

  async register(dto: RegisterDto) {
    const existingUser = await this.prisma.user.findUnique({ where: { email: dto.email } });

    if (existingUser) {
      throw new ConflictException("Email is already registered");
    }

    const passwordHash = await bcrypt.hash(dto.password, 12);

    const user = await this.prisma.$transaction(async (tx) => {
      const createdUser = await tx.user.create({
        data: {
          email: dto.email,
          name: dto.name,
          passwordHash,
          role: Role.OWNER
        }
      });

      await tx.workspace.create({
        data: {
          name: `${dto.name}'s Workspace`,
          ownerId: createdUser.id,
          members: {
            create: {
              userId: createdUser.id,
              role: Role.OWNER
            }
          }
        }
      });

      return createdUser;
    });

    return this.createAuthResponse(user);
  }

  async login(dto: LoginDto) {
    const user = await this.prisma.user.findUnique({ where: { email: dto.email } });

    if (!user) {
      throw new UnauthorizedException("Invalid credentials");
    }

    const passwordMatches = await bcrypt.compare(dto.password, user.passwordHash);

    if (!passwordMatches) {
      throw new UnauthorizedException("Invalid credentials");
    }

    return this.createAuthResponse(user);
  }

  async refresh(rawToken: string) {
    const tokenHash = hashToken(rawToken);
    const stored = await this.prisma.refreshToken.findUnique({ where: { tokenHash } });

    if (!stored) {
      throw new UnauthorizedException("Invalid refresh token");
    }

    if (stored.expiresAt < new Date()) {
      await this.prisma.refreshToken.delete({ where: { id: stored.id } });
      throw new UnauthorizedException("Refresh token has expired — please log in again");
    }

    const user = await this.prisma.user.findUniqueOrThrow({ where: { id: stored.userId } });

    // Rotate: delete old, issue new
    await this.prisma.refreshToken.delete({ where: { id: stored.id } });

    return this.createAuthResponse(user);
  }

  async logout(rawToken: string): Promise<void> {
    const tokenHash = hashToken(rawToken);
    const stored = await this.prisma.refreshToken.findUnique({
      where: { tokenHash },
      select: { id: true }
    });

    if (stored) {
      await this.prisma.refreshToken.delete({ where: { id: stored.id } });
    }
  }

  private async createAuthResponse(user: User) {
    const accessToken = this.jwtService.sign(
      { sub: user.id, email: user.email, role: user.role },
      { expiresIn: this.config.get("JWT_EXPIRES_IN", "15m") }
    );

    const rawRefreshToken = randomBytes(REFRESH_TOKEN_BYTES).toString("hex");
    const tokenHash = hashToken(rawRefreshToken);
    const expiresAt = new Date(Date.now() + REFRESH_TOKEN_TTL_DAYS * 86_400_000);

    await this.prisma.refreshToken.create({
      data: { userId: user.id, tokenHash, expiresAt }
    });

    return {
      accessToken,
      refreshToken: rawRefreshToken,
      user: toSafeUser(user)
    };
  }
}
