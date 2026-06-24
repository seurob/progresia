import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { JwtService } from "@nestjs/jwt";
import { Request } from "express";

export interface AdminJwtPayload {
  sub: string;
  email: string;
  role: string;
  type: string;
}

export interface AdminRequest extends Request {
  admin: AdminJwtPayload;
}

@Injectable()
export class AdminJwtGuard implements CanActivate {
  constructor(
    private readonly jwtService: JwtService,
    private readonly config: ConfigService
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<AdminRequest>();
    const token = this.extractToken(request);

    if (!token) {
      throw new UnauthorizedException("Admin access required");
    }

    const secret = this.config.get<string>("ADMIN_JWT_SECRET", "admin_change_me");

    try {
      const payload = await this.jwtService.verifyAsync<AdminJwtPayload>(token, { secret });
      if (payload.type !== "admin") throw new Error();
      request.admin = payload;
      return true;
    } catch {
      throw new UnauthorizedException("Admin access required");
    }
  }

  private extractToken(request: Request): string | undefined {
    const auth = request.headers.authorization;
    if (!auth) return undefined;
    const [type, token] = auth.split(" ");
    return type === "Bearer" ? token : undefined;
  }
}
