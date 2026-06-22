import { Body, Controller, HttpCode, HttpStatus, Post, Req } from "@nestjs/common";
import { ApiCreatedResponse, ApiNoContentResponse, ApiOkResponse, ApiTags } from "@nestjs/swagger";
import { Request } from "express";
import { AuthService } from "./auth.service";
import { ChangePendingEmailDto } from "./dto/change-pending-email.dto";
import { LoginDto } from "./dto/login.dto";
import { RefreshDto } from "./dto/refresh.dto";
import { RegisterDto } from "./dto/register.dto";
import { ResendVerificationCodeDto } from "./dto/resend-verification-code.dto";
import { VerifyEmailDto } from "./dto/verify-email.dto";

@ApiTags("auth")
@Controller("auth")
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post("register")
  @ApiCreatedResponse({ description: "Creates a pending user and sends an email verification code." })
  register(@Body() dto: RegisterDto, @Req() req: Request) {
    return this.authService.register(dto, req.ip);
  }

  @Post("login")
  @HttpCode(HttpStatus.OK)
  @ApiOkResponse({ description: "Returns access + refresh tokens for valid credentials." })
  login(@Body() dto: LoginDto, @Req() req: Request) {
    return this.authService.login(dto, req.ip);
  }

  @Post("verify-email")
  @HttpCode(HttpStatus.OK)
  @ApiOkResponse({ description: "Verifies a pending account email code." })
  verifyEmail(@Body() dto: VerifyEmailDto) {
    return this.authService.verifyEmail(dto);
  }

  @Post("resend-verification-code")
  @HttpCode(HttpStatus.OK)
  @ApiOkResponse({ description: "Sends a new verification code when the account is pending." })
  resendVerificationCode(@Body() dto: ResendVerificationCodeDto, @Req() req: Request) {
    return this.authService.resendVerificationCode(dto, req.ip);
  }

  @Post("change-pending-email")
  @HttpCode(HttpStatus.OK)
  @ApiOkResponse({ description: "Changes the email for a pending account and sends a new code." })
  changePendingEmail(@Body() dto: ChangePendingEmailDto, @Req() req: Request) {
    return this.authService.changePendingEmail(dto, req.ip);
  }

  @Post("refresh")
  @HttpCode(HttpStatus.OK)
  @ApiOkResponse({ description: "Rotates the refresh token and issues a new access token." })
  refresh(@Body() dto: RefreshDto) {
    return this.authService.refresh(dto.refreshToken);
  }

  @Post("logout")
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiNoContentResponse({ description: "Invalidates the refresh token." })
  async logout(@Body() dto: RefreshDto) {
    await this.authService.logout(dto.refreshToken);
  }
}
