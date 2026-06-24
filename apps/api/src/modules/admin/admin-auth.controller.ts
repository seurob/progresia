import { Body, Controller, Get, HttpCode, HttpStatus, Post, Req, UseGuards } from "@nestjs/common";
import { ApiTags } from "@nestjs/swagger";
import { AdminAuthService } from "./admin-auth.service";
import { AdminLoginDto } from "./dto/admin-login.dto";
import { AdminJwtGuard, AdminRequest } from "./guards/admin-jwt.guard";

@ApiTags("admin-auth")
@Controller("admin/auth")
export class AdminAuthController {
  constructor(private readonly adminAuthService: AdminAuthService) {}

  @Post("login")
  @HttpCode(HttpStatus.OK)
  login(@Body() dto: AdminLoginDto) {
    return this.adminAuthService.login(dto);
  }

  @Get("me")
  @UseGuards(AdminJwtGuard)
  me(@Req() req: AdminRequest) {
    return this.adminAuthService.me(req.admin.sub);
  }

  @Post("logout")
  @HttpCode(HttpStatus.NO_CONTENT)
  logout() {
    // Admin token is stateless — the client discards it on logout
  }
}
