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
  UseGuards
} from "@nestjs/common";
import { ApiTags } from "@nestjs/swagger";
import { AdminProjectsService } from "./admin-projects.service";
import { AdminCreateProjectDto } from "./dto/admin-create-project.dto";
import { AdminUpdateProjectDto } from "./dto/admin-update-project.dto";
import { AdminJwtGuard } from "./guards/admin-jwt.guard";

@ApiTags("admin-projects")
@Controller("admin/projects")
@UseGuards(AdminJwtGuard)
export class AdminProjectsController {
  constructor(private readonly adminProjectsService: AdminProjectsService) {}

  @Get()
  findAll(@Query("search") search?: string) {
    return this.adminProjectsService.findAll(search);
  }

  @Post()
  create(@Body() dto: AdminCreateProjectDto) {
    return this.adminProjectsService.create(dto);
  }

  @Patch(":id")
  update(@Param("id") id: string, @Body() dto: AdminUpdateProjectDto) {
    return this.adminProjectsService.update(id, dto);
  }

  @Delete(":id")
  @HttpCode(HttpStatus.NO_CONTENT)
  async remove(@Param("id") id: string) {
    await this.adminProjectsService.remove(id);
  }
}
