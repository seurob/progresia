import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  Patch,
  Post,
  Query,
  Req,
  UseGuards
} from "@nestjs/common";
import { ApiTags } from "@nestjs/swagger";
import { AdminUsersService } from "./admin-users.service";
import { AdminCreateUserDto } from "./dto/admin-create-user.dto";
import { AdminUpdateUserDto } from "./dto/admin-update-user.dto";
import { AdminJwtGuard, AdminRequest } from "./guards/admin-jwt.guard";

@ApiTags("admin-users")
@Controller("admin/users")
@UseGuards(AdminJwtGuard)
export class AdminUsersController {
  constructor(private readonly adminUsersService: AdminUsersService) {}

  @Get()
  findAll(@Query("search") search?: string) {
    return this.adminUsersService.findAll(search);
  }

  @Post()
  create(@Body() dto: AdminCreateUserDto) {
    return this.adminUsersService.create(dto);
  }

  @Patch(":id")
  update(@Param("id") id: string, @Body() dto: AdminUpdateUserDto, @Req() req: AdminRequest) {
    return this.adminUsersService.update(id, dto, req.admin.sub);
  }

  @Delete(":id")
  @HttpCode(HttpStatus.NO_CONTENT)
  async remove(@Param("id") id: string, @Req() req: AdminRequest) {
    await this.adminUsersService.remove(id, req.admin.sub);
  }
}
