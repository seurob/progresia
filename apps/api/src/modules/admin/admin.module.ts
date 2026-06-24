import { Module } from "@nestjs/common";
import { AdminAuthController } from "./admin-auth.controller";
import { AdminUsersController } from "./admin-users.controller";
import { AdminProjectsController } from "./admin-projects.controller";
import { AdminAuthService } from "./admin-auth.service";
import { AdminUsersService } from "./admin-users.service";
import { AdminProjectsService } from "./admin-projects.service";
import { AdminJwtGuard } from "./guards/admin-jwt.guard";

// JwtService and ConfigService are available globally via AuthModule (@Global) and ConfigModule.forRoot({ isGlobal: true })
@Module({
  controllers: [AdminAuthController, AdminUsersController, AdminProjectsController],
  providers: [AdminAuthService, AdminUsersService, AdminProjectsService, AdminJwtGuard]
})
export class AdminModule {}
