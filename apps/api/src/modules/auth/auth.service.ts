import { BadRequestException, ConflictException, HttpException, HttpStatus, Injectable, UnauthorizedException } from "@nestjs/common";
import { JwtService } from "@nestjs/jwt";
import { ConfigService } from "@nestjs/config";
import { AccountStatus, Role, User } from "@prisma/client";
import * as bcrypt from "bcryptjs";
import { createHash, randomBytes, randomInt, timingSafeEqual } from "node:crypto";
import { PrismaService } from "../../database/prisma.service";
import { toSafeUser } from "../../common/users/safe-user";
import { CaptchaService } from "./captcha.service";
import { ChangePendingEmailDto } from "./dto/change-pending-email.dto";
import { LoginDto } from "./dto/login.dto";
import { RegisterDto } from "./dto/register.dto";
import { ResendVerificationCodeDto } from "./dto/resend-verification-code.dto";
import { VerifyEmailDto } from "./dto/verify-email.dto";
import { EmailService } from "./email.service";

const REFRESH_TOKEN_TTL_DAYS = 7;
const REFRESH_TOKEN_BYTES = 48;
const VERIFY_CODE_TTL_MINUTES = 15;
const RESEND_COOLDOWN_MS = 60_000;
const RESEND_LIMIT_HOUR = 5;

function hashToken(raw: string): string {
  return createHash("sha256").update(raw).digest("hex");
}

function safeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  return left.length === right.length && timingSafeEqual(left, right);
}

@Injectable()
export class AuthService {
  private readonly resendAttempts = new Map<string, number[]>();

  constructor(
    private readonly prisma: PrismaService,
    private readonly jwtService: JwtService,
    private readonly config: ConfigService,
    private readonly captcha: CaptchaService,
    private readonly email: EmailService
  ) {}

  async register(dto: RegisterDto, remoteIp?: string) {
    await this.captcha.verify(dto.captchaToken, remoteIp);

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
          role: Role.OWNER,
          accountStatus: AccountStatus.PENDING_VERIFICATION,
          emailVerified: false
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

    await this.issueVerificationCode(user);

    return {
      requiresEmailVerification: true,
      email: user.email,
      message: "Revisa tu correo electronico e introduce el codigo de verificacion."
    };
  }

  async login(dto: LoginDto, remoteIp?: string) {
    await this.captcha.verify(dto.captchaToken, remoteIp);

    const user = await this.prisma.user.findUnique({ where: { email: dto.email } });

    if (!user) {
      throw new UnauthorizedException("Invalid credentials");
    }

    const passwordMatches = await bcrypt.compare(dto.password, user.passwordHash);

    if (!passwordMatches) {
      throw new UnauthorizedException("Invalid credentials");
    }

    if (!user.emailVerified || user.accountStatus !== AccountStatus.ACTIVE) {
      throw new UnauthorizedException(
        "Debes verificar tu correo electronico antes de iniciar sesion. Revisa tu bandeja de entrada o solicita un nuevo codigo de verificacion."
      );
    }

    return this.createAuthResponse(user);
  }

  async verifyEmail(dto: VerifyEmailDto) {
    const user = await this.prisma.user.findUnique({ where: { email: dto.email } });

    if (!user) {
      throw new BadRequestException("Codigo de verificacion no valido");
    }

    const record = await this.prisma.emailVerificationCode.findFirst({
      where: {
        userId: user.id,
        verifiedAt: null,
        invalidatedAt: null
      },
      orderBy: { createdAt: "desc" }
    });

    if (!record || record.expiresAt < new Date() || record.attempts >= record.maxAttempts) {
      throw new BadRequestException("Codigo de verificacion no valido o caducado");
    }

    const matches = safeEqual(record.codeHash, hashToken(dto.code));
    if (!matches) {
      await this.prisma.emailVerificationCode.update({
        where: { id: record.id },
        data: { attempts: { increment: 1 } }
      });
      throw new BadRequestException("Codigo de verificacion no valido o caducado");
    }

    const now = new Date();
    const [, updatedUser] = await this.prisma.$transaction([
      this.prisma.emailVerificationCode.update({
        where: { id: record.id },
        data: { verifiedAt: now, invalidatedAt: now }
      }),
      this.prisma.user.update({
        where: { id: user.id },
        data: {
          emailVerified: true,
          emailVerifiedAt: now,
          accountStatus: AccountStatus.ACTIVE
        }
      })
    ]);

    return {
      verified: true,
      user: toSafeUser(updatedUser)
    };
  }

  async resendVerificationCode(dto: ResendVerificationCodeDto, remoteIp?: string) {
    await this.captcha.verify(dto.captchaToken, remoteIp);
    this.enforceResendRateLimit(dto.email);

    const user = await this.prisma.user.findUnique({ where: { email: dto.email } });

    if (user && (!user.emailVerified || user.accountStatus === AccountStatus.PENDING_VERIFICATION)) {
      await this.issueVerificationCode(user);
    }

    return {
      sent: true,
      message: "Si la cuenta esta pendiente de verificacion, enviaremos un nuevo codigo."
    };
  }

  async changePendingEmail(dto: ChangePendingEmailDto, remoteIp?: string) {
    await this.captcha.verify(dto.captchaToken, remoteIp);

    const user = await this.prisma.user.findUnique({ where: { email: dto.currentEmail } });
    if (!user || user.emailVerified || user.accountStatus !== AccountStatus.PENDING_VERIFICATION) {
      throw new BadRequestException("No se pudo actualizar el correo pendiente");
    }

    const passwordMatches = await bcrypt.compare(dto.password, user.passwordHash);
    if (!passwordMatches) {
      throw new BadRequestException("No se pudo actualizar el correo pendiente");
    }

    const duplicate = await this.prisma.user.findUnique({ where: { email: dto.newEmail } });
    if (duplicate) {
      throw new ConflictException("Email is already registered");
    }

    const updatedUser = await this.prisma.$transaction(async (tx) => {
      await tx.emailVerificationCode.updateMany({
        where: { userId: user.id, verifiedAt: null, invalidatedAt: null },
        data: { invalidatedAt: new Date() }
      });

      return tx.user.update({
        where: { id: user.id },
        data: { email: dto.newEmail }
      });
    });

    await this.issueVerificationCode(updatedUser);

    return {
      email: updatedUser.email,
      message: "Correo actualizado. Revisa el nuevo buzon para verificar la cuenta."
    };
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

  private enforceResendRateLimit(email: string) {
    const key = email.toLowerCase();
    const now = Date.now();
    const attempts = (this.resendAttempts.get(key) ?? []).filter((ts) => now - ts < 3_600_000);
    const last = attempts.at(-1);

    if (last && now - last < RESEND_COOLDOWN_MS) {
      throw new HttpException("Espera antes de solicitar un nuevo codigo.", HttpStatus.TOO_MANY_REQUESTS);
    }

    if (attempts.length >= RESEND_LIMIT_HOUR) {
      throw new HttpException("Has solicitado demasiados codigos. Intentalo mas tarde.", HttpStatus.TOO_MANY_REQUESTS);
    }

    attempts.push(now);
    this.resendAttempts.set(key, attempts);
  }

  private generateVerificationCode() {
    return randomInt(100_000, 1_000_000).toString();
  }

  private async issueVerificationCode(user: User) {
    const code = this.generateVerificationCode();
    const expiresAt = new Date(Date.now() + VERIFY_CODE_TTL_MINUTES * 60_000);

    await this.prisma.$transaction([
      this.prisma.emailVerificationCode.updateMany({
        where: { userId: user.id, verifiedAt: null, invalidatedAt: null },
        data: { invalidatedAt: new Date() }
      }),
      this.prisma.emailVerificationCode.create({
        data: {
          userId: user.id,
          codeHash: hashToken(code),
          expiresAt,
          maxAttempts: 5
        }
      })
    ]);

    await this.email.sendVerificationCode(user.email, user.name, code, VERIFY_CODE_TTL_MINUTES);
  }
}
